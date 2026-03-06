import type { Cookies, RequestEvent } from '@sveltejs/kit';
import { dev } from '$app/environment';

export const AUTH_COOKIE_NAME = 'cyt_access_token';
export const AUTH_REFRESH_COOKIE_NAME = 'cyt_refresh_token';
const ACCESS_COOKIE_MAX_AGE_SECONDS = 60 * 20;
const REFRESH_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30;

function getBackendBaseURL(): string {
	const value = process.env.API_BASE_URL || process.env.VITE_API_BASE_URL || 'http://localhost:8000';
	return value.endsWith('/') ? value.slice(0, -1) : value;
}

export function setAuthCookie(cookies: Cookies, token: string): void {
	cookies.set(AUTH_COOKIE_NAME, token, {
		path: '/',
		httpOnly: true,
		sameSite: 'lax',
		secure: !dev,
		maxAge: ACCESS_COOKIE_MAX_AGE_SECONDS
	});
}

export function setRefreshAuthCookie(cookies: Cookies, token: string): void {
	cookies.set(AUTH_REFRESH_COOKIE_NAME, token, {
		path: '/',
		httpOnly: true,
		sameSite: 'lax',
		secure: !dev,
		maxAge: REFRESH_COOKIE_MAX_AGE_SECONDS
	});
}

export function clearAuthCookie(cookies: Cookies): void {
	cookies.delete(AUTH_COOKIE_NAME, {
		path: '/'
	});
}

export function clearRefreshAuthCookie(cookies: Cookies): void {
	cookies.delete(AUTH_REFRESH_COOKIE_NAME, {
		path: '/'
	});
}

export function getAuthToken(cookies: Cookies): string | undefined {
	return cookies.get(AUTH_COOKIE_NAME);
}

export function getRefreshAuthToken(cookies: Cookies): string | undefined {
	return cookies.get(AUTH_REFRESH_COOKIE_NAME);
}

export type BackendFetchOptions = {
	path: string;
	method?: string;
	headers?: HeadersInit;
	body?: BodyInit | null;
	token?: string;
};

export async function backendFetch(options: BackendFetchOptions): Promise<Response> {
	const { path, method = 'GET', headers, body, token } = options;
	const targetPath = path.startsWith('/') ? path : `/${path}`;
	const url = `${getBackendBaseURL()}${targetPath}`;

	const finalHeaders = new Headers(headers ?? {});
	if (token) {
		finalHeaders.set('Authorization', `Bearer ${token}`);
	}

	return fetch(url, {
		method,
		headers: finalHeaders,
		body
	});
}

export async function backendFetchFromEvent(
	event: RequestEvent,
	path: string,
	init: Omit<BackendFetchOptions, 'path' | 'token'> = {}
): Promise<Response> {
	const token = getAuthToken(event.cookies);
	return backendFetch({
		path,
		...init,
		token
	});
}

export function mapAuthError(detail: unknown): string {
	if (typeof detail === 'string') return detail;
	if (detail && typeof detail === 'object' && 'code' in detail && typeof detail.code === 'string') {
		return detail.code;
	}
	return 'AUTH_UNKNOWN_ERROR';
}

export async function refreshAuthSession(event: RequestEvent): Promise<boolean> {
	const refreshToken = getRefreshAuthToken(event.cookies);
	if (!refreshToken) return false;

	try {
		const response = await backendFetch({
			path: '/auth/session/refresh',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ refresh_token: refreshToken })
		});

		if (!response.ok) {
			clearAuthCookie(event.cookies);
			clearRefreshAuthCookie(event.cookies);
			event.locals.authToken = null;
			return false;
		}

		const data = (await response.json()) as {
			access_token: string;
			refresh_token: string;
		};

		setAuthCookie(event.cookies, data.access_token);
		setRefreshAuthCookie(event.cookies, data.refresh_token);
		event.locals.authToken = data.access_token;
		return true;
	} catch {
		clearAuthCookie(event.cookies);
		clearRefreshAuthCookie(event.cookies);
		event.locals.authToken = null;
		return false;
	}
}
