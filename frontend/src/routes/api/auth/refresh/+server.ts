import { json, type RequestHandler } from '@sveltejs/kit';
import {
	backendFetch,
	clearAuthCookie,
	clearRefreshAuthCookie,
	getRefreshAuthToken,
	mapAuthError,
	setAuthCookie,
	setRefreshAuthCookie
} from '$lib/server/auth';

export const POST: RequestHandler = async (event) => {
	const refreshToken = getRefreshAuthToken(event.cookies);
	if (!refreshToken) {
		clearAuthCookie(event.cookies);
		clearRefreshAuthCookie(event.cookies);
		return json({ error: 'UNAUTHENTICATED' }, { status: 401 });
	}

	const response = await backendFetch({
		path: '/auth/session/refresh',
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ refresh_token: refreshToken })
	});

	if (!response.ok) {
		const payload = await response.json().catch(() => ({ detail: 'REFRESH_FAILED' }));
		clearAuthCookie(event.cookies);
		clearRefreshAuthCookie(event.cookies);
		return json({ error: mapAuthError(payload.detail) }, { status: response.status });
	}

	const data = (await response.json()) as {
		access_token: string;
		refresh_token: string;
		access_expires_in?: number;
		refresh_expires_in?: number;
	};
	setAuthCookie(event.cookies, data.access_token, event.url, data.access_expires_in);
	setRefreshAuthCookie(event.cookies, data.refresh_token, event.url, data.refresh_expires_in);
	return json({ ok: true });
};
