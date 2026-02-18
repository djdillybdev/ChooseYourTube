import { json, type RequestHandler } from '@sveltejs/kit';
import { backendFetchFromEvent, clearAuthCookie } from '$lib/server/auth';

export const POST: RequestHandler = async (event) => {
	const token = event.locals.authToken;

	if (token) {
		await backendFetchFromEvent(event, '/auth/jwt/logout', {
			method: 'POST'
		}).catch(() => undefined);
	}

	clearAuthCookie(event.cookies);
	return json({ ok: true });
};
