import { beforeEach, describe, expect, it, vi } from 'vitest';

const { backendFetchMock, setAuthCookieMock, setRefreshAuthCookieMock, mapAuthErrorMock } =
	vi.hoisted(() => ({
		backendFetchMock: vi.fn(),
		setAuthCookieMock: vi.fn(),
		setRefreshAuthCookieMock: vi.fn(),
		mapAuthErrorMock: vi.fn(
			(payload: { detail?: string }) => payload.detail ?? 'AUTH_REQUEST_FAILED'
		)
	}));

vi.mock('$lib/server/auth', () => ({
	backendFetch: backendFetchMock,
	setAuthCookie: setAuthCookieMock,
	setRefreshAuthCookie: setRefreshAuthCookieMock,
	mapAuthError: mapAuthErrorMock
}));

import { actions as loginActions } from '../../../src/routes/login/+page.server';
import { actions as registerActions } from '../../../src/routes/register/+page.server';

function formRequest(path: string, fields: Record<string, string>): Request {
	return new Request(`http://localhost${path}`, {
		method: 'POST',
		headers: { 'content-type': 'application/x-www-form-urlencoded' },
		body: new URLSearchParams(fields)
	});
}

describe('authentication form actions', () => {
	beforeEach(() => {
		backendFetchMock.mockReset();
		setAuthCookieMock.mockReset();
		setRefreshAuthCookieMock.mockReset();
		mapAuthErrorMock.mockClear();
	});

	it('logs in, sets both secure session cookies, and preserves a safe return path', async () => {
		backendFetchMock.mockResolvedValue(
			Response.json({ access_token: 'access', refresh_token: 'refresh' })
		);

		await expect(
			loginActions.default!({
				request: formRequest('/login', {
					email: ' person@example.com ',
					password: 'secret',
					next: '/channels/channel-1?q=history'
				}),
				cookies: {},
				url: new URL('https://example.test/login')
			} as never)
		).rejects.toMatchObject({ status: 303, location: '/channels/channel-1?q=history' });

		expect(setAuthCookieMock).toHaveBeenCalledWith(
			expect.anything(),
			'access',
			expect.any(URL),
			undefined
		);
		expect(setRefreshAuthCookieMock).toHaveBeenCalled();
	});

	it('rejects an external-looking return URL and maps credential failures to plain language', async () => {
		backendFetchMock.mockResolvedValue(
			Response.json({ detail: 'INVALID_CREDENTIALS' }, { status: 401 })
		);

		const result = await loginActions.default!({
			request: formRequest('/login', {
				email: 'person@example.com',
				password: 'wrong',
				next: '//malicious.example'
			}),
			cookies: {},
			url: new URL('http://localhost/login')
		} as never);

		expect(result).toMatchObject({
			status: 401,
			data: { email: 'person@example.com', message: 'Email or password is incorrect.' }
		});
		expect(setAuthCookieMock).not.toHaveBeenCalled();
	});

	it('validates registration password confirmation before calling the backend', async () => {
		const result = await registerActions.default!({
			request: formRequest('/register', {
				email: 'person@example.com',
				password: 'one',
				confirmPassword: 'two'
			})
		} as never);

		expect(result).toMatchObject({
			status: 400,
			data: { fieldErrors: { confirmPassword: 'Passwords must match.' } }
		});
		expect(backendFetchMock).not.toHaveBeenCalled();
	});

	it('keeps the email and maps a duplicate registration response', async () => {
		backendFetchMock.mockResolvedValue(
			Response.json({ detail: 'EMAIL_ALREADY_REGISTERED' }, { status: 409 })
		);

		const result = await registerActions.default!({
			request: formRequest('/register', {
				email: 'person@example.com',
				password: 'password',
				confirmPassword: 'password'
			})
		} as never);

		expect(result).toMatchObject({
			status: 409,
			data: {
				email: 'person@example.com',
				message: 'An account with this email already exists.'
			}
		});
	});
});
