import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetch, clearAccess, clearRefresh, mapAuthError } = vi.hoisted(() => ({
	backendFetch: vi.fn(),
	clearAccess: vi.fn(),
	clearRefresh: vi.fn(),
	mapAuthError: vi.fn(() => 'CURRENT_PASSWORD_INVALID')
}));

vi.mock('$lib/server/auth', () => ({
	backendFetchFromEvent: backendFetch,
	clearAuthCookie: clearAccess,
	clearRefreshAuthCookie: clearRefresh,
	mapAuthError
}));

import { DELETE } from '../../../../../../src/routes/api/auth/account/+server';

describe('DELETE /api/auth/account', () => {
	beforeEach(() => vi.clearAllMocks());

	it('forwards password verification and clears both cookies on success', async () => {
		backendFetch.mockResolvedValue(new Response(null, { status: 204 }));
		const request = new Request('https://example.test/api/auth/account', {
			method: 'DELETE',
			body: JSON.stringify({ current_password: 'secret' })
		});
		const event = { request, cookies: {} } as any;
		const response = await DELETE(event);

		expect(backendFetch).toHaveBeenCalledWith(event, '/users/me', {
			method: 'DELETE',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ current_password: 'secret' })
		});
		expect(clearAccess).toHaveBeenCalledWith(event.cookies);
		expect(clearRefresh).toHaveBeenCalledWith(event.cookies);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('preserves cookies and maps malformed failures', async () => {
		backendFetch.mockResolvedValue(new Response('bad gateway', { status: 502 }));
		const event = {
			request: new Request('https://example.test', { method: 'DELETE', body: '{}' }),
			cookies: {}
		} as any;
		const response = await DELETE(event);
		expect(response.status).toBe(502);
		expect(mapAuthError).toHaveBeenCalledWith({ code: 'AUTH_REQUEST_FAILED' });
		expect(clearAccess).not.toHaveBeenCalled();
	});
});
