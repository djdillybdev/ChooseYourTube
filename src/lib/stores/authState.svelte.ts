import { authApi } from '$lib/api/auth';
import type { UserRead } from '$lib/types/api';

export type AuthStatus = 'unknown' | 'authenticated' | 'unauthenticated';

class AuthState {
	status = $state<AuthStatus>('unknown');
	user = $state<UserRead | null>(null);

	setAuthenticated(user: UserRead): void {
		this.status = 'authenticated';
		this.user = user;
	}

	setUnauthenticated(): void {
		this.status = 'unauthenticated';
		this.user = null;
	}

	async initialize(): Promise<void> {
		const user = await authApi.me();
		if (user) {
			this.setAuthenticated(user);
			return;
		}
		this.setUnauthenticated();
	}

	async logout(): Promise<void> {
		await authApi.logout();
		this.setUnauthenticated();
	}
}

export const authState = new AuthState();
