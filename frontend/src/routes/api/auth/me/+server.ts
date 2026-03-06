import { json, type RequestHandler } from '@sveltejs/kit';
import {
	backendFetchFromEvent,
	clearAuthCookie,
	clearRefreshAuthCookie,
	refreshAuthSession
} from '$lib/server/auth';

export const GET: RequestHandler = async (event) => {
	if (!event.locals.authToken) {
		const refreshed = await refreshAuthSession(event);
		if (!refreshed) {
			return json({ error: 'UNAUTHENTICATED' }, { status: 401 });
		}
	}

	let response = await backendFetchFromEvent(event, '/users/me');

	if (response.status === 401) {
		const refreshed = await refreshAuthSession(event);
		if (!refreshed) {
			clearAuthCookie(event.cookies);
			clearRefreshAuthCookie(event.cookies);
			return json({ error: 'UNAUTHENTICATED' }, { status: 401 });
		}
		response = await backendFetchFromEvent(event, '/users/me');
	}

	if (!response.ok) {
		const payload = await response.json().catch(() => ({ error: 'ME_FAILED' }));
		return json(payload, { status: response.status });
	}

	const user = await response.json();
	return json(user);
};
