import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetchFromEventMock, clearAuthCookieMock } = vi.hoisted(() => ({
	backendFetchFromEventMock: vi.fn(),
	clearAuthCookieMock: vi.fn()
}));

vi.mock('$lib/server/auth', () => ({
	backendFetchFromEvent: backendFetchFromEventMock,
	clearAuthCookie: clearAuthCookieMock
}));

import { POST } from '../../../../../../src/routes/api/auth/logout/+server';

function createEvent(token: string | null) {
	return {
		locals: { authToken: token },
		cookies: {}
	} as any;
}

describe('POST /api/auth/logout', () => {
	beforeEach(() => {
		backendFetchFromEventMock.mockReset();
		clearAuthCookieMock.mockReset();
	});

	it('calls backend logout when token exists and clears cookie', async () => {
		backendFetchFromEventMock.mockResolvedValue(new Response(null, { status: 204 }));
		const event = createEvent('token-1');

		const response = await POST(event);

		expect(backendFetchFromEventMock).toHaveBeenCalledWith(event, '/auth/jwt/logout', {
			method: 'POST'
		});
		expect(clearAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('still clears cookie when token is missing', async () => {
		const event = createEvent(null);

		const response = await POST(event);

		expect(backendFetchFromEventMock).not.toHaveBeenCalled();
		expect(clearAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(response.status).toBe(200);
	});

	it('swallows backend logout failures and returns ok', async () => {
		backendFetchFromEventMock.mockRejectedValue(new Error('network failed'));
		const event = createEvent('token-1');

		const response = await POST(event);

		expect(clearAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ ok: true });
	});
});
