import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthAPI } from '../../../../src/lib/api/auth';

describe('AuthAPI', () => {
	const fetchMock = vi.fn<typeof fetch>();
	const api = new AuthAPI();

	beforeEach(() => {
		fetchMock.mockReset();
		vi.stubGlobal('fetch', fetchMock);
	});

	it('login posts credentials and returns ok=true on success', async () => {
		fetchMock.mockResolvedValue(new Response(null, { status: 200 }));

		const result = await api.login('me@example.com', 'pw');

		expect(fetchMock).toHaveBeenCalledWith('/api/auth/login', {
			method: 'POST',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email: 'me@example.com', password: 'pw' })
		});
		expect(result).toEqual({ ok: true });
	});

	it('register returns mapped error payload when request fails', async () => {
		fetchMock.mockResolvedValue(
			new Response(JSON.stringify({ error: 'EMAIL_ALREADY_EXISTS' }), {
				status: 400,
				headers: { 'content-type': 'application/json' }
			})
		);

		const result = await api.register('dup@example.com', 'pw');

		expect(result).toEqual({ ok: false, error: 'EMAIL_ALREADY_EXISTS' });
	});

	it('logout posts to logout endpoint', async () => {
		fetchMock.mockResolvedValue(new Response(null, { status: 200 }));

		await api.logout();

		expect(fetchMock).toHaveBeenCalledWith('/api/auth/logout', {
			method: 'POST',
			credentials: 'include'
		});
	});

	it('me returns user payload when authenticated', async () => {
		fetchMock.mockResolvedValue(
			new Response(JSON.stringify({ id: 'u1', email: 'me@example.com' }), {
				status: 200,
				headers: { 'content-type': 'application/json' }
			})
		);

		await expect(api.me()).resolves.toEqual({ id: 'u1', email: 'me@example.com' });
	});

	it('me returns null when unauthenticated', async () => {
		fetchMock.mockResolvedValue(new Response(null, { status: 401 }));

		await expect(api.me()).resolves.toBeNull();
	});
});
