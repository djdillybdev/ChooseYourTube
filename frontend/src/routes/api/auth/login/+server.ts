import { json, type RequestHandler } from '@sveltejs/kit';
import {
	backendFetch,
	mapAuthError,
	setAuthCookie,
	setRefreshAuthCookie
} from '$lib/server/auth';

export const POST: RequestHandler = async ({ request, cookies }) => {
	const { email, password } = await request.json();

	const response = await backendFetch({
		path: '/auth/session/login',
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ email, password })
	});

	if (!response.ok) {
		const payload = await response.json().catch(() => ({ detail: 'LOGIN_FAILED' }));
		return json({ error: mapAuthError(payload.detail) }, { status: response.status });
	}

	const data = (await response.json()) as {
		access_token: string;
		refresh_token: string;
		token_type: string;
	};
	setAuthCookie(cookies, data.access_token);
	setRefreshAuthCookie(cookies, data.refresh_token);

	return json({ ok: true });
};
