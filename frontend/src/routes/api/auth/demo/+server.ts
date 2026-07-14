import { json, type RequestHandler } from '@sveltejs/kit';
import { backendFetch, mapAuthError, setAuthCookie, setRefreshAuthCookie } from '$lib/server/auth';

export const POST: RequestHandler = async ({ cookies, url }) => {
	const response = await backendFetch({ path: '/auth/demo', method: 'POST' });
	if (!response.ok) {
		const payload = await response.json().catch(() => ({ code: 'DEMO_ACCOUNT_UNAVAILABLE' }));
		return json({ error: mapAuthError(payload) }, { status: response.status });
	}
	const data = (await response.json()) as {
		access_token: string;
		refresh_token: string;
		access_expires_in?: number;
		refresh_expires_in?: number;
	};
	setAuthCookie(cookies, data.access_token, url, data.access_expires_in);
	setRefreshAuthCookie(cookies, data.refresh_token, url, data.refresh_expires_in);
	return json({ ok: true });
};
