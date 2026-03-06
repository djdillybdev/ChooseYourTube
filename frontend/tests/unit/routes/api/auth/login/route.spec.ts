import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetchMock, setAuthCookieMock, setRefreshAuthCookieMock, mapAuthErrorMock } = vi.hoisted(
	() => ({
	backendFetchMock: vi.fn(),
	setAuthCookieMock: vi.fn(),
	setRefreshAuthCookieMock: vi.fn(),
	mapAuthErrorMock: vi.fn((detail: unknown) => String(detail ?? 'AUTH_UNKNOWN_ERROR'))
	})
);

vi.mock('$lib/server/auth', () => ({
	backendFetch: backendFetchMock,
	setAuthCookie: setAuthCookieMock,
	setRefreshAuthCookie: setRefreshAuthCookieMock,
	mapAuthError: mapAuthErrorMock
}));

import { POST } from '../../../../../../src/routes/api/auth/login/+server';

describe('POST /api/auth/login', () => {
	beforeEach(() => {
		backendFetchMock.mockReset();
		setAuthCookieMock.mockReset();
		setRefreshAuthCookieMock.mockReset();
		mapAuthErrorMock.mockClear();
	});

	it('returns ok and sets auth cookie on successful login', async () => {
		backendFetchMock.mockResolvedValue(
			new Response(JSON.stringify({ access_token: 'token-1', refresh_token: 'refresh-1' }), {
				status: 200,
				headers: { 'content-type': 'application/json' }
			})
		);

		const response = await POST({
			request: new Request('http://localhost/api/auth/login', {
				method: 'POST',
				body: JSON.stringify({ email: 'me@example.com', password: 'pw' }),
				headers: { 'content-type': 'application/json' }
			}),
			cookies: {}
		} as any);

		expect(backendFetchMock).toHaveBeenCalledWith(
			expect.objectContaining({
				path: '/auth/session/login',
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			})
		);
		expect(setAuthCookieMock).toHaveBeenCalledWith(expect.anything(), 'token-1');
		expect(setRefreshAuthCookieMock).toHaveBeenCalledWith(expect.anything(), 'refresh-1');
		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('maps backend errors and returns same status code', async () => {
		backendFetchMock.mockResolvedValue(
			new Response(JSON.stringify({ detail: 'INVALID_CREDENTIALS' }), {
				status: 401,
				headers: { 'content-type': 'application/json' }
			})
		);

		const response = await POST({
			request: new Request('http://localhost/api/auth/login', {
				method: 'POST',
				body: JSON.stringify({ email: 'me@example.com', password: 'bad' }),
				headers: { 'content-type': 'application/json' }
			}),
			cookies: {}
		} as any);

		expect(mapAuthErrorMock).toHaveBeenCalledWith('INVALID_CREDENTIALS');
		expect(setAuthCookieMock).not.toHaveBeenCalled();
		expect(response.status).toBe(401);
		expect(await response.json()).toEqual({ error: 'INVALID_CREDENTIALS' });
	});
});
