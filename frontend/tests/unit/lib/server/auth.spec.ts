import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('$app/environment', () => ({
	dev: false
}));

import {
	AUTH_COOKIE_NAME,
	backendFetch,
	clearAuthCookie,
	getAuthToken,
	mapAuthError,
	setAuthCookie
} from '../../../../src/lib/server/auth';
import { server } from '../../../msw/server';

describe('auth helpers', () => {
	afterEach(() => {
		delete process.env.API_BASE_URL;
		delete process.env.VITE_API_BASE_URL;
	});

	it('sets, gets and clears auth cookie', () => {
		const set = vi.fn();
		const get = vi.fn(() => 'abc123');
		const del = vi.fn();
		const cookies = { set, get, delete: del };

		setAuthCookie(cookies as any, 'abc123');
		expect(set).toHaveBeenCalledWith(
			AUTH_COOKIE_NAME,
			'abc123',
			expect.objectContaining({
				path: '/',
				httpOnly: true,
				sameSite: 'lax'
			})
		);

		expect(getAuthToken(cookies as any)).toBe('abc123');

		clearAuthCookie(cookies as any);
		expect(del).toHaveBeenCalledWith(AUTH_COOKIE_NAME, { path: '/' });
	});

	it('sets secure cookies for an HTTPS request URL', () => {
		const set = vi.fn();
		const cookies = { set };

		setAuthCookie(cookies as any, 'secure-token', new URL('https://demo.example.com/login'));

		expect(set).toHaveBeenCalledWith(
			AUTH_COOKIE_NAME,
			'secure-token',
			expect.objectContaining({ httpOnly: true, sameSite: 'lax', secure: true })
		);
	});

	it('maps auth error details to stable string values', () => {
		expect(mapAuthError('BAD_CREDENTIALS')).toBe('BAD_CREDENTIALS');
		expect(mapAuthError({ code: 'INVALID_TOKEN' })).toBe('INVALID_TOKEN');
		expect(mapAuthError({ foo: 'bar' })).toBe('AUTH_UNKNOWN_ERROR');
	});

	it('calls backend with normalized path and bearer token', async () => {
		process.env.API_BASE_URL = 'http://api.test/';

		server.use(
			http.get('http://api.test/users/me', ({ request }) => {
				expect(request.headers.get('authorization')).toBe('Bearer token-1');
				return HttpResponse.json({ ok: true });
			})
		);

		const response = await backendFetch({
			path: 'users/me',
			token: 'token-1'
		});

		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('forwards method, headers and body', async () => {
		process.env.API_BASE_URL = 'http://api.test';

		server.use(
			http.post('http://api.test/auth/register', async ({ request }) => {
				expect(request.headers.get('content-type')).toContain('application/json');
				expect(await request.text()).toBe('{"email":"a@b.com"}');
				return HttpResponse.json({ created: true }, { status: 201 });
			})
		);

		const response = await backendFetch({
			path: '/auth/register',
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email: 'a@b.com' })
		});

		expect(response.status).toBe(201);
	});
});
