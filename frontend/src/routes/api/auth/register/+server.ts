import { json, type RequestHandler } from '@sveltejs/kit';
import { backendFetch, mapAuthError } from '$lib/server/auth';

export const POST: RequestHandler = async ({ request }) => {
	const { email, password } = await request.json();

	const response = await backendFetch({
		path: '/auth/register',
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ email, password })
	});

	if (!response.ok) {
		const payload = await response.json().catch(() => ({ detail: 'REGISTER_FAILED' }));
		return json({ error: mapAuthError(payload.detail) }, { status: response.status });
	}

	return json({ ok: true }, { status: 201 });
};
