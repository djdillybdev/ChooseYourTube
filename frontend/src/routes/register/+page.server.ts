import { backendFetch, mapAuthError } from '$lib/server/auth';
import { authMessage } from '$lib/utils/authMessages';
import { fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';

export const actions: Actions = {
	default: async ({ request }) => {
		const values = await request.formData();
		const email = String(values.get('email') ?? '').trim();
		const password = String(values.get('password') ?? '');
		const confirmPassword = String(values.get('confirmPassword') ?? '');

		const fieldErrors = {
			email: email ? undefined : 'Enter your email address.',
			password: password ? undefined : 'Enter a password.',
			confirmPassword:
				confirmPassword && confirmPassword === password ? undefined : 'Passwords must match.'
		};
		if (fieldErrors.email || fieldErrors.password || fieldErrors.confirmPassword) {
			return fail(400, {
				email,
				message: 'Check the highlighted fields and try again.',
				fieldErrors
			});
		}

		let response: Response;
		try {
			response = await backendFetch({
				path: '/auth/register',
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

		throw redirect(303, '/login?registered=1');
	}
};
