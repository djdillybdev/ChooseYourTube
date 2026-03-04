import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetchMock, mapAuthErrorMock } = vi.hoisted(() => ({
	backendFetchMock: vi.fn(),
	mapAuthErrorMock: vi.fn((detail: unknown) => String(detail ?? 'AUTH_UNKNOWN_ERROR'))
}));

vi.mock('$lib/server/auth', () => ({
	backendFetch: backendFetchMock,
	mapAuthError: mapAuthErrorMock
}));

import { POST } from '../../../../../../src/routes/api/auth/register/+server';

describe('POST /api/auth/register', () => {
	beforeEach(() => {
		backendFetchMock.mockReset();
		mapAuthErrorMock.mockClear();
	});

	it('returns 201 when backend register succeeds', async () => {
		backendFetchMock.mockResolvedValue(new Response(null, { status: 201 }));

		const response = await POST({
			request: new Request('http://localhost/api/auth/register', {
				method: 'POST',
				body: JSON.stringify({ email: 'me@example.com', password: 'pw' }),
				headers: { 'content-type': 'application/json' }
			})
		} as any);

		expect(backendFetchMock).toHaveBeenCalledWith(
			expect.objectContaining({
				path: '/auth/register',
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email: 'me@example.com', password: 'pw' })
			})
		);
		expect(response.status).toBe(201);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('maps backend register errors', async () => {
		backendFetchMock.mockResolvedValue(
			new Response(JSON.stringify({ detail: 'EMAIL_ALREADY_EXISTS' }), {
				status: 400,
				headers: { 'content-type': 'application/json' }
			})
		);

		const response = await POST({
			request: new Request('http://localhost/api/auth/register', {
				method: 'POST',
				body: JSON.stringify({ email: 'dup@example.com', password: 'pw' }),
				headers: { 'content-type': 'application/json' }
			})
		} as any);

		expect(mapAuthErrorMock).toHaveBeenCalledWith('EMAIL_ALREADY_EXISTS');
		expect(response.status).toBe(400);
		expect(await response.json()).toEqual({ error: 'EMAIL_ALREADY_EXISTS' });
	});
});
