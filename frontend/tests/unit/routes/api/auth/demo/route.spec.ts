import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetch, mapAuthError, setAccess, setRefresh } = vi.hoisted(() => ({
	backendFetch: vi.fn(),
	mapAuthError: vi.fn(() => 'DEMO_ACCOUNT_UNAVAILABLE'),
	setAccess: vi.fn(),
	setRefresh: vi.fn()
}));

vi.mock('$lib/server/auth', () => ({
	backendFetch,
	mapAuthError,
	setAuthCookie: setAccess,
	setRefreshAuthCookie: setRefresh
}));

import { POST } from '../../../../../../src/routes/api/auth/demo/+server';

describe('POST /api/auth/demo', () => {
	beforeEach(() => vi.clearAllMocks());

	it('creates the same access and refresh cookie shape as password login', async () => {
		backendFetch.mockResolvedValue(
			new Response(
				JSON.stringify({
					access_token: 'access',
					refresh_token: 'refresh',
					access_expires_in: 60,
					refresh_expires_in: 120
				}),
				{ status: 200 }
			)
		);
		const event = { cookies: {}, url: new URL('https://example.test/api/auth/demo') } as any;
		const response = await POST(event);

		expect(backendFetch).toHaveBeenCalledWith({ path: '/auth/demo', method: 'POST' });
		expect(setAccess).toHaveBeenCalledWith(event.cookies, 'access', event.url, 60);
		expect(setRefresh).toHaveBeenCalledWith(event.cookies, 'refresh', event.url, 120);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('maps safe backend and malformed failures', async () => {
		backendFetch.mockResolvedValue(new Response('not-json', { status: 503 }));
		const response = await POST({ cookies: {}, url: new URL('https://example.test') } as any);
		expect(response.status).toBe(503);
		expect(mapAuthError).toHaveBeenCalledWith({ code: 'DEMO_ACCOUNT_UNAVAILABLE' });
		expect(setAccess).not.toHaveBeenCalled();
	});
});
