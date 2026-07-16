import { backendFetch, mapAuthError, setAuthCookie, setRefreshAuthCookie } from '$lib/server/auth';
import { authMessage } from '$lib/utils/authMessages';
import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';

function safeNextPath(value: FormDataEntryValue | null): string {
	if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//')) {
		return '/inbox';
	}
	return value;
}

export const actions: Actions = {
	default: async ({ request, cookies, url }) => {
		const values = await request.formData();
		const email = String(values.get('email') ?? '').trim();
		const password = String(values.get('password') ?? '');
		const next = safeNextPath(values.get('next'));

		if (!email || !password) {
			return fail(400, {
				email,
				message: 'Enter your email and password.',
				fieldErrors: {
					email: email ? undefined : 'Enter your email address.',
					password: password ? undefined : 'Enter your password.'
				}
			});
		}

		let response: Response;
		try {
			response = await backendFetch({
				path: '/auth/session/login',
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password })
			});
		} catch {
			return fail(503, { email, message: authMessage('AUTH_REQUEST_FAILED') });
		}

		if (!response.ok) {
			const payload = await response.json().catch(() => ({ detail: 'AUTH_REQUEST_FAILED' }));
			return fail(response.status, { email, message: authMessage(mapAuthError(payload)) });
		}

		const data = (await response.json()) as {
			access_token: string;
			refresh_token: string;
			access_expires_in?: number;
			refresh_expires_in?: number;
		};
		setAuthCookie(cookies, data.access_token, url, data.access_expires_in);
		setRefreshAuthCookie(cookies, data.refresh_token, url, data.refresh_expires_in);

		throw redirect(303, next);
	}
};
