import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetchFromEventMock, refreshAuthSessionMock } = vi.hoisted(() => ({
	backendFetchFromEventMock: vi.fn(),
	refreshAuthSessionMock: vi.fn()
}));

vi.mock('$lib/server/auth', () => ({
	backendFetchFromEvent: backendFetchFromEventMock,
	refreshAuthSession: refreshAuthSessionMock
}));

import { GET, POST } from '../../../../../../src/routes/api/backend/[...path]/+server';

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
		refreshAuthSessionMock.mockReset();
	});

	it('returns 404 for disallowed proxied paths', async () => {
		const response = await GET(makeEvent('/api/backend/admin/secret'));

		expect(response.status).toBe(404);
		expect(await response.json()).toEqual({ error: 'PROXY_PATH_NOT_ALLOWED' });
		expect(backendFetchFromEventMock).not.toHaveBeenCalled();
	});

	it('proxies allowed GET requests and strips content-length', async () => {
		backendFetchFromEventMock.mockResolvedValue(
			new Response(JSON.stringify({ ok: true }), {
				status: 200,
				headers: {
					'content-type': 'application/json',
					'content-length': '18',
					'x-test': 'pass'
				}
			})
		);

		const response = await GET(makeEvent('/api/backend/videos?limit=10'));

		expect(backendFetchFromEventMock).toHaveBeenCalledWith(
			expect.anything(),
			'/videos?limit=10',
			expect.objectContaining({ method: 'GET', body: undefined })
		);
		expect(response.headers.get('x-test')).toBe('pass');
		expect(response.headers.get('content-length')).toBeNull();
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
			'/channels',
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

	it('retries once on 401 after successful refresh', async () => {
		refreshAuthSessionMock.mockResolvedValue(true);
		backendFetchFromEventMock
			.mockResolvedValueOnce(new Response(null, { status: 401 }))
			.mockResolvedValueOnce(
				new Response(JSON.stringify({ ok: true }), {
					status: 200,
					headers: { 'content-type': 'application/json' }
				})
			);

		const response = await GET(makeEvent('/api/backend/videos'));
		expect(refreshAuthSessionMock).toHaveBeenCalledOnce();
		expect(backendFetchFromEventMock).toHaveBeenCalledTimes(2);
		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ ok: true });
	});
});
