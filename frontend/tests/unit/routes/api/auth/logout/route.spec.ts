import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
	backendFetchMock,
	clearAuthCookieMock,
	clearRefreshAuthCookieMock,
	getRefreshAuthTokenMock
} = vi.hoisted(() => ({
	backendFetchMock: vi.fn(),
	clearAuthCookieMock: vi.fn(),
	clearRefreshAuthCookieMock: vi.fn(),
	getRefreshAuthTokenMock: vi.fn()
}));

vi.mock('$lib/server/auth', () => ({
	backendFetch: backendFetchMock,
	clearAuthCookie: clearAuthCookieMock,
	clearRefreshAuthCookie: clearRefreshAuthCookieMock,
	getRefreshAuthToken: getRefreshAuthTokenMock
}));

import { POST } from '../../../../../../src/routes/api/auth/logout/+server';

function createEvent() {
	return {
		cookies: {}
	} as any;
}

describe('POST /api/auth/logout', () => {
	beforeEach(() => {
		backendFetchMock.mockReset();
		clearAuthCookieMock.mockReset();
		clearRefreshAuthCookieMock.mockReset();
		getRefreshAuthTokenMock.mockReset();
	});

	it('calls backend logout when refresh token exists and clears cookies', async () => {
		backendFetchMock.mockResolvedValue(new Response(null, { status: 204 }));
		getRefreshAuthTokenMock.mockReturnValue('refresh-1');
		const event = createEvent();

		const response = await POST(event);

		expect(backendFetchMock).toHaveBeenCalledWith({
			path: '/auth/session/logout',
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ refresh_token: 'refresh-1' })
		});
		expect(clearAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(clearRefreshAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('still clears cookies when refresh token is missing', async () => {
		getRefreshAuthTokenMock.mockReturnValue(undefined);
		const event = createEvent();

		const response = await POST(event);

		expect(backendFetchMock).not.toHaveBeenCalled();
		expect(clearAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(clearRefreshAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(response.status).toBe(200);
	});

	it('swallows backend logout failures and returns ok', async () => {
		backendFetchMock.mockRejectedValue(new Error('network failed'));
		getRefreshAuthTokenMock.mockReturnValue('refresh-1');
		const event = createEvent();

		const response = await POST(event);

		expect(clearAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(clearRefreshAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ ok: true });
	});
});
