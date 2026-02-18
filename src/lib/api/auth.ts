import type { UserRead } from '$lib/types/api';

interface AuthResult {
	ok: boolean;
	error?: string;
}

async function parseResponse(response: Response): Promise<AuthResult> {
	if (response.ok) {
		return { ok: true };
	}

	const payload = await response.json().catch(() => ({ error: 'AUTH_REQUEST_FAILED' }));
	return { ok: false, error: payload.error ?? 'AUTH_REQUEST_FAILED' };
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
