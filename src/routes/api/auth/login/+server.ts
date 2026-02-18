import { json, type RequestHandler } from '@sveltejs/kit';
import { backendFetch, mapAuthError, setAuthCookie } from '$lib/server/auth';

export const POST: RequestHandler = async ({ request, cookies }) => {
	const { email, password } = await request.json();

	const body = new URLSearchParams({
		username: email,
		password
	});

	const response = await backendFetch({
		path: '/auth/jwt/login',
		method: 'POST',
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded'
		},
		body
	});

	if (!response.ok) {
		const payload = await response.json().catch(() => ({ detail: 'LOGIN_FAILED' }));
		return json({ error: mapAuthError(payload.detail) }, { status: response.status });
	}

	const data = (await response.json()) as { access_token: string; token_type: string };
	setAuthCookie(cookies, data.access_token);

	return json({ ok: true });
};
