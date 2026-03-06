import { describe, expect, it, vi } from 'vitest';

vi.mock('$lib/server/auth', () => ({
	AUTH_COOKIE_NAME: 'cyt_access_token',
	AUTH_REFRESH_COOKIE_NAME: 'cyt_refresh_token'
}));

import { handle } from '../../src/hooks.server';

const AUTH_COOKIE_NAME = 'cyt_access_token';
const AUTH_REFRESH_COOKIE_NAME = 'cyt_refresh_token';

function createEvent(path: string, token?: string, refreshToken?: string) {
	const url = new URL(`http://localhost${path}`);
	return {
		url,
		cookies: {
			get: vi.fn((name: string) => {
				if (name === AUTH_COOKIE_NAME) return token;
				if (name === AUTH_REFRESH_COOKIE_NAME) return refreshToken;
				return undefined;
			})
		},
		locals: {}
	} as any;
}

describe('hooks.server handle', () => {
	it('returns 401 for unauthenticated API requests', async () => {
		const event = createEvent('/api/backend/videos');
		const resolve = vi.fn();

		const response = await handle({ event, resolve } as any);

		expect(response.status).toBe(401);
		expect(await response.json()).toEqual({ error: 'UNAUTHENTICATED' });
		expect(resolve).not.toHaveBeenCalled();
	});

	it('redirects unauthenticated page requests to login with next param', async () => {
		const event = createEvent('/inbox?page=2');
		const resolve = vi.fn();

		await expect(handle({ event, resolve } as any)).rejects.toMatchObject({
			status: 307,
			location: '/login?next=%2Finbox%3Fpage%3D2'
		});
	});

	it('redirects authenticated user away from login/register', async () => {
		const event = createEvent('/login', 'abc');
		const resolve = vi.fn();

		await expect(handle({ event, resolve } as any)).rejects.toMatchObject({
			status: 307,
			location: '/inbox'
		});
	});

	it('allows request to resolve when only refresh token exists', async () => {
		const event = createEvent('/inbox', undefined, 'refresh-1');
		const resolved = new Response('ok');
		const resolve = vi.fn(async () => resolved);

		const response = await handle({ event, resolve } as any);

		expect(resolve).toHaveBeenCalledOnce();
		expect(response).toBe(resolved);
	});

	it('calls resolve for allowed public paths', async () => {
		const event = createEvent('/robots.txt');
		const resolved = new Response('ok');
		const resolve = vi.fn(async () => resolved);

		const response = await handle({ event, resolve } as any);

		expect(resolve).toHaveBeenCalledOnce();
		expect(response).toBe(resolved);
	});
});
