import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetchFromEventMock } = vi.hoisted(() => ({
	backendFetchFromEventMock: vi.fn()
}));

vi.mock('$lib/server/auth', () => ({
	backendFetchFromEvent: backendFetchFromEventMock
}));

import {
	GET,
	POST,
	trailingSlash
} from '../../../../../../src/routes/api/backend/[...path]/+server';

function makeEvent(path: string, init?: { method?: string; body?: string; contentType?: string }) {
	const request = new Request(`http://localhost${path}`, {
		method: init?.method ?? 'GET',
		body: init?.body,
		headers: init?.contentType ? { 'content-type': init.contentType } : undefined
	});

	return {
		url: new URL(`http://localhost${path}`),
		request
	} as any;
}

describe('backend proxy route', () => {
	beforeEach(() => {
		backendFetchFromEventMock.mockReset();
	});

	it('returns 404 for disallowed proxied paths', async () => {
		const response = await GET(makeEvent('/api/backend/admin/secret'));

		expect(response.status).toBe(404);
		expect(await response.json()).toEqual({ error: 'PROXY_PATH_NOT_ALLOWED' });
		expect(backendFetchFromEventMock).not.toHaveBeenCalled();
	});

	it('proxies collection requests canonically and strips stale representation headers', async () => {
		backendFetchFromEventMock.mockResolvedValue(
			new Response(JSON.stringify({ ok: true }), {
				status: 200,
				headers: {
					'content-type': 'application/json',
					'content-encoding': 'br',
					'content-length': '18',
					'transfer-encoding': 'chunked',
					'x-test': 'pass'
				}
			})
		);

		const response = await GET(makeEvent('/api/backend/videos?limit=10'));

		expect(backendFetchFromEventMock).toHaveBeenCalledWith(
			expect.anything(),
			'/videos/?limit=10',
			expect.objectContaining({ method: 'GET', body: undefined })
		);
		expect(trailingSlash).toBe('ignore');
		expect(response.headers.get('x-test')).toBe('pass');
		expect(response.headers.get('content-encoding')).toBeNull();
		expect(response.headers.get('content-length')).toBeNull();
		expect(response.headers.get('transfer-encoding')).toBeNull();
		expect(response.headers.get('cache-control')).toBe('private, no-store');
		expect(response.headers.get('server-timing')).toMatch(/^backend;dur=/);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('proxies synchronization status requests', async () => {
		backendFetchFromEventMock.mockResolvedValue(
			new Response(JSON.stringify({ status: 'running' }), {
				status: 200,
				headers: { 'content-type': 'application/json' }
			})
		);

		const response = await GET(makeEvent('/api/backend/sync-runs/run-id'));
		expect(response.status).toBe(200);
		expect(backendFetchFromEventMock).toHaveBeenCalledWith(
			expect.anything(),
			'/sync-runs/run-id',
			expect.objectContaining({ method: 'GET' })
		);
	});

	it('preserves detail paths without appending a trailing slash', async () => {
		backendFetchFromEventMock.mockResolvedValue(
			new Response(JSON.stringify({ id: 'video-1' }), {
				status: 200,
				headers: { 'content-type': 'application/json' }
			})
		);

		await GET(makeEvent('/api/backend/videos/video-1'));

		expect(backendFetchFromEventMock).toHaveBeenCalledWith(
			expect.anything(),
			'/videos/video-1',
			expect.objectContaining({ method: 'GET' })
		);
	});

	it('forwards body and content-type for POST requests', async () => {
		backendFetchFromEventMock.mockResolvedValue(new Response(null, { status: 204 }));

		const response = await POST(
			makeEvent('/api/backend/channels', {
				method: 'POST',
				body: JSON.stringify({ handle: '@abc' }),
				contentType: 'application/json'
			})
		);

		expect(response.status).toBe(204);
		expect(backendFetchFromEventMock).toHaveBeenCalledWith(
			expect.anything(),
			'/channels/',
			expect.objectContaining({
				method: 'POST',
				body: expect.any(Blob),
				headers: { 'Content-Type': 'application/json' }
			})
		);
		const forwarded = backendFetchFromEventMock.mock.calls[0][2].body as Blob;
		expect(await forwarded.text()).toBe(JSON.stringify({ handle: '@abc' }));
	});

	it('allows imports and preserves multipart bytes and boundary', async () => {
		backendFetchFromEventMock.mockResolvedValue(
			new Response(JSON.stringify({ import: { id: 'import-1' } }), {
				status: 201,
				headers: { 'content-type': 'application/json' }
			})
		);
		const response = await POST(
			makeEvent('/api/backend/imports/subscriptions/csv', {
				method: 'POST',
				body: '--boundary\r\nCSV data\r\n--boundary--',
				contentType: 'multipart/form-data; boundary=boundary'
			})
		);
		expect(response.status).toBe(201);
		expect(backendFetchFromEventMock).toHaveBeenCalledWith(
			expect.anything(),
			'/imports/subscriptions/csv',
			expect.objectContaining({
				headers: { 'Content-Type': 'multipart/form-data; boundary=boundary' },
				body: expect.any(Blob)
			})
		);
		const forwarded = backendFetchFromEventMock.mock.calls[0][2].body as Blob;
		expect(await forwarded.text()).toBe('--boundary\r\nCSV data\r\n--boundary--');
	});

	it('returns 401 without rotating refresh tokens in the generic proxy', async () => {
		backendFetchFromEventMock.mockResolvedValueOnce(new Response(null, { status: 401 }));

		const response = await GET(makeEvent('/api/backend/videos'));
		expect(backendFetchFromEventMock).toHaveBeenCalledOnce();
		expect(response.status).toBe(401);
	});
});
