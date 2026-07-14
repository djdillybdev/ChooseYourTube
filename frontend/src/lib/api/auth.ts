import type { UserRead } from '$lib/types/api';

interface AuthResult {
	ok: boolean;
	error?: string;
}

const AUTH_MESSAGES: Record<string, string> = {
	INVALID_CREDENTIALS: 'Email or password is incorrect.',
	EMAIL_ALREADY_REGISTERED: 'An account with this email already exists.',
	EMAIL_ALREADY_EXISTS: 'An account with this email already exists.',
	REGISTER_USER_ALREADY_EXISTS: 'An account with this email already exists.',
	INVALID_PASSWORD: 'Choose a stronger password and try again.',
	CURRENT_PASSWORD_INVALID: 'The current password is incorrect.',
	DEMO_ACCOUNT_UNAVAILABLE: 'The demo account is temporarily unavailable. Please try again.',
	VALIDATION_ERROR: 'Check the information you entered and try again.',
	AUTH_REQUEST_FAILED: 'Authentication could not be completed. Please try again.'
};

async function parseResponse(response: Response): Promise<AuthResult> {
	if (response.ok) {
		return { ok: true };
	}

	const payload = await response.json().catch(() => ({ error: 'AUTH_REQUEST_FAILED' }));
	const code = payload.error ?? 'AUTH_REQUEST_FAILED';
	return { ok: false, error: AUTH_MESSAGES[code] ?? AUTH_MESSAGES.AUTH_REQUEST_FAILED };
}

export class AuthAPI {
	async login(email: string, password: string): Promise<AuthResult> {
		const response = await fetch('/api/auth/login', {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email, password })
		});

		return parseResponse(response);
	}

	async register(email: string, password: string): Promise<AuthResult> {
		const response = await fetch('/api/auth/register', {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email, password })
		});

		return parseResponse(response);
	}

	async demoLogin(): Promise<AuthResult> {
		const response = await fetch('/api/auth/demo', {
			method: 'POST',
			credentials: 'include'
		});
		return parseResponse(response);
	}

	async deleteAccount(currentPassword: string): Promise<AuthResult> {
		const response = await fetch('/api/auth/account', {
			method: 'DELETE',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ current_password: currentPassword })
		});
		return parseResponse(response);
	}

	async logout(): Promise<void> {
		await fetch('/api/auth/logout', {
			method: 'POST',
			credentials: 'include'
		});
	}

	async me(): Promise<UserRead | null> {
		const response = await fetch('/api/auth/me', { credentials: 'include' });
		if (!response.ok) return null;
		return (await response.json()) as UserRead;
	}
}

export const authApi = new AuthAPI();
