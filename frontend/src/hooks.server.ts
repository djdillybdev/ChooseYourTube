import type { Handle } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import { AUTH_COOKIE_NAME } from '$lib/server/auth';

const PUBLIC_PATHS = ['/login', '/register'];

function isPublicPath(pathname: string): boolean {
	if (PUBLIC_PATHS.includes(pathname)) return true;
	if (pathname.startsWith('/api/auth/')) return true;
	if (pathname.startsWith('/_app/')) return true;
	if (pathname.startsWith('/favicon')) return true;
	if (pathname === '/robots.txt') return true;
	return false;
}

export const handle: Handle = async ({ event, resolve }) => {
	const { pathname, search } = event.url;
	const token = event.cookies.get(AUTH_COOKIE_NAME);

	event.locals.authToken = token ?? null;

	if (!isPublicPath(pathname) && !token) {
		if (pathname.startsWith('/api/')) {
			return new Response(JSON.stringify({ error: 'UNAUTHENTICATED' }), {
				status: 401,
				headers: {
					'Content-Type': 'application/json'
				}
			});
		}
		const next = encodeURIComponent(`${pathname}${search}`);
		throw redirect(307, `/login?next=${next}`);
	}

	if (token && (pathname === '/login' || pathname === '/register')) {
		throw redirect(307, '/inbox');
	}

	return resolve(event);
};
