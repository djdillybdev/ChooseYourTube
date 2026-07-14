import { json, type RequestHandler } from '@sveltejs/kit';
import {
	backendFetchFromEvent,
	clearAuthCookie,
	clearRefreshAuthCookie,
	mapAuthError
} from '$lib/server/auth';

export const DELETE: RequestHandler = async (event) => {
	const payload = await event.request.text();
	const response = await backendFetchFromEvent(event, '/users/me', {
		method: 'DELETE',
		headers: { 'Content-Type': 'application/json' },
		body: payload
	});
	if (!response.ok) {
		const error = await response.json().catch(() => ({ code: 'AUTH_REQUEST_FAILED' }));
		return json({ error: mapAuthError(error) }, { status: response.status });
	}
	clearAuthCookie(event.cookies);
	clearRefreshAuthCookie(event.cookies);
	return json({ ok: true });
};
