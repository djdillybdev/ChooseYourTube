import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetchFromEventMock, clearAuthCookieMock } = vi.hoisted(() => ({
	backendFetchFromEventMock: vi.fn(),
	clearAuthCookieMock: vi.fn()
}));

vi.mock('$lib/server/auth', () => ({
	backendFetchFromEvent: backendFetchFromEventMock,
	clearAuthCookie: clearAuthCookieMock
}));

import { GET } from '../../../../../../src/routes/api/auth/me/+server';

function createEvent(token: string | null) {
	return {
		locals: { authToken: token },
		cookies: {}
	} as any;
}

describe('GET /api/auth/me', () => {
	beforeEach(() => {
		backendFetchFromEventMock.mockReset();
		clearAuthCookieMock.mockReset();
	});

	it('returns 401 if no auth token exists', async () => {
		const response = await GET(createEvent(null));

		expect(response.status).toBe(401);
		expect(await response.json()).toEqual({ error: 'UNAUTHENTICATED' });
		expect(backendFetchFromEventMock).not.toHaveBeenCalled();
	});

	it('clears cookie and returns 401 when backend returns 401', async () => {
		backendFetchFromEventMock.mockResolvedValue(new Response(null, { status: 401 }));
		const event = createEvent('token-1');

		const response = await GET(event);

		expect(clearAuthCookieMock).toHaveBeenCalledWith(event.cookies);
		expect(response.status).toBe(401);
		expect(await response.json()).toEqual({ error: 'UNAUTHENTICATED' });
	});

	it('returns backend payload for non-401 failures', async () => {
		backendFetchFromEventMock.mockResolvedValue(
			new Response(JSON.stringify({ error: 'ME_FAILED' }), {
				status: 500,
				headers: { 'content-type': 'application/json' }
			})
		);

		const response = await GET(createEvent('token-1'));

		expect(response.status).toBe(500);
		expect(await response.json()).toEqual({ error: 'ME_FAILED' });
	});

	it('returns user payload on success', async () => {
		backendFetchFromEventMock.mockResolvedValue(
			new Response(JSON.stringify({ id: 'u1', email: 'me@example.com' }), {
				status: 200,
				headers: { 'content-type': 'application/json' }
			})
		);

		const response = await GET(createEvent('token-1'));

		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ id: 'u1', email: 'me@example.com' });
	});
});
