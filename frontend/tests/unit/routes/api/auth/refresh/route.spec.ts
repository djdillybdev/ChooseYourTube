import { beforeEach, describe, expect, it, vi } from 'vitest';

const auth = vi.hoisted(() => ({
	backendFetch: vi.fn(),
	clearAccess: vi.fn(),
	clearRefresh: vi.fn(),
	getRefresh: vi.fn(),
	mapAuthError: vi.fn((value) => value),
	setAccess: vi.fn(),
	setRefresh: vi.fn()
}));

vi.mock('$lib/server/auth', () => ({
	backendFetch: auth.backendFetch,
	clearAuthCookie: auth.clearAccess,
	clearRefreshAuthCookie: auth.clearRefresh,
	getRefreshAuthToken: auth.getRefresh,
	mapAuthError: auth.mapAuthError,
	setAuthCookie: auth.setAccess,
	setRefreshAuthCookie: auth.setRefresh
}));

import { POST } from '../../../../../../src/routes/api/auth/refresh/+server';

describe('POST /api/auth/refresh', () => {
	beforeEach(() => vi.clearAllMocks());

	it('clears stale cookies when no refresh session exists', async () => {
		auth.getRefresh.mockReturnValue(null);
		const event = { cookies: {}, url: new URL('https://example.test') } as any;
		const response = await POST(event);
		expect(response.status).toBe(401);
		expect(auth.clearAccess).toHaveBeenCalledWith(event.cookies);
		expect(auth.clearRefresh).toHaveBeenCalledWith(event.cookies);
	});

	it('rotates both cookies after a successful refresh', async () => {
		auth.getRefresh.mockReturnValue('old-refresh');
		auth.backendFetch.mockResolvedValue(
			new Response(JSON.stringify({ access_token: 'new-access', refresh_token: 'new-refresh' }), {
				status: 200
			})
		);
		const event = { cookies: {}, url: new URL('https://example.test') } as any;
		const response = await POST(event);
		expect(auth.setAccess).toHaveBeenCalledWith(event.cookies, 'new-access', event.url, undefined);
		expect(auth.setRefresh).toHaveBeenCalledWith(
			event.cookies,
			'new-refresh',
			event.url,
			undefined
		);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('clears the session and maps invalid refresh responses', async () => {
		auth.getRefresh.mockReturnValue('expired');
		auth.backendFetch.mockResolvedValue(
			new Response(JSON.stringify({ detail: 'REFRESH_TOKEN_REUSED' }), { status: 401 })
		);
		const event = { cookies: {}, url: new URL('https://example.test') } as any;
		const response = await POST(event);
		expect(response.status).toBe(401);
		expect(auth.mapAuthError).toHaveBeenCalledWith('REFRESH_TOKEN_REUSED');
		expect(auth.clearAccess).toHaveBeenCalled();
		expect(auth.clearRefresh).toHaveBeenCalled();
	});
});
