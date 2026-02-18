import type { Cookies, RequestEvent } from '@sveltejs/kit';
import { dev } from '$app/environment';

export const AUTH_COOKIE_NAME = 'cyt_access_token';

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
		maxAge: 60 * 60 * 24 * 7
	});
}

export function clearAuthCookie(cookies: Cookies): void {
	cookies.delete(AUTH_COOKIE_NAME, {
		path: '/'
	});
}

export function getAuthToken(cookies: Cookies): string | undefined {
	return cookies.get(AUTH_COOKIE_NAME);
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
