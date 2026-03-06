import { json, type RequestHandler } from '@sveltejs/kit';
import {
	backendFetch,
	clearAuthCookie,
	clearRefreshAuthCookie,
	getRefreshAuthToken
} from '$lib/server/auth';

export const POST: RequestHandler = async (event) => {
	const refreshToken = getRefreshAuthToken(event.cookies);

	if (refreshToken) {
		await backendFetch({
			path: '/auth/session/logout',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ refresh_token: refreshToken })
		}).catch(() => undefined);
	}

	clearAuthCookie(event.cookies);
	clearRefreshAuthCookie(event.cookies);
	return json({ ok: true });
};
