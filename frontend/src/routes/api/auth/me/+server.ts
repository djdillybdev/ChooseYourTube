import { json, type RequestHandler } from '@sveltejs/kit';
import { backendFetchFromEvent, clearAuthCookie } from '$lib/server/auth';

export const GET: RequestHandler = async (event) => {
	if (!event.locals.authToken) {
		return json({ error: 'UNAUTHENTICATED' }, { status: 401 });
	}

	const response = await backendFetchFromEvent(event, '/users/me');

	if (response.status === 401) {
		clearAuthCookie(event.cookies);
		return json({ error: 'UNAUTHENTICATED' }, { status: 401 });
	}

	if (!response.ok) {
		const payload = await response.json().catch(() => ({ error: 'ME_FAILED' }));
		return json(payload, { status: response.status });
	}

	const user = await response.json();
	return json(user);
};
