import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetchFromEventMock } = vi.hoisted(() => ({ backendFetchFromEventMock: vi.fn() }));

vi.mock('$lib/server/auth', () => ({
	backendFetchFromEvent: backendFetchFromEventMock
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
				body: JSON.stringify({ handle: '@abc' }),
				headers: { 'Content-Type': 'application/json' }
			})
		);
	});
});
