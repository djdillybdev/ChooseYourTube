import { json, type RequestEvent } from '@sveltejs/kit';
import { backendFetchFromEvent } from '$lib/server/auth';

const ALLOWED_PREFIXES = [
	'videos',
	'channels',
	'folders',
	'categories',
	'tags',
	'playlists',
	'sync-runs',
	'imports',
	'users/me'
];

const TRAILING_SLASH_COLLECTIONS = new Set([
	'videos',
	'channels',
	'folders',
	'categories',
	'tags',
	'playlists'
]);

export const trailingSlash = 'ignore';

function isAllowed(path: string): boolean {
	return ALLOWED_PREFIXES.some((prefix) => path === prefix || path.startsWith(`${prefix}/`));
}

async function proxy(event: RequestEvent, method: string) {
	const startedAt = performance.now();
	const rawPath = event.url.pathname.replace(/^\/api\/backend\/?/, '');
	const normalizedPath = rawPath.replace(/\/+$/, '');

	if (!normalizedPath || !isAllowed(normalizedPath)) {
		return json({ error: 'PROXY_PATH_NOT_ALLOWED' }, { status: 404 });
	}

	const query = event.url.search || '';
	const backendPath = TRAILING_SLASH_COLLECTIONS.has(normalizedPath)
		? `/${normalizedPath}/`
		: `/${normalizedPath}`;
	const body =
		method === 'GET' || method === 'DELETE'
			? undefined
			: new Blob([await event.request.arrayBuffer()]);
	const contentType = event.request.headers.get('content-type');

	const response = await backendFetchFromEvent(event, `${backendPath}${query}`, {
		method,
		headers: contentType ? { 'Content-Type': contentType } : undefined,
		body
	});

	const headers = new Headers(response.headers);
	const upstreamContentEncoding = headers.get('content-encoding');
	// Node's fetch transparently decodes upstream response bodies but retains
	// the representation headers. Forwarding those headers makes the browser
	// attempt to decode an already-decoded body.
	headers.delete('content-encoding');
	headers.delete('content-length');
	headers.delete('transfer-encoding');
	headers.set('Cache-Control', 'private, no-store');
	const durationMs = Math.round((performance.now() - startedAt) * 100) / 100;
	headers.append('Server-Timing', `backend;dur=${durationMs}`);
	console.info(
		JSON.stringify({
			message: 'backend_proxy_completed',
			method,
			path: `/${normalizedPath}`,
			backend_path: backendPath,
			status: response.status,
			upstream_content_encoding: upstreamContentEncoding,
			upstream_redirected: response.redirected,
			duration_ms: durationMs,
			region: process.env.VERCEL_REGION ?? process.env.AWS_REGION ?? 'local'
		})
	);

	return new Response(response.body, {
		status: response.status,
		headers
	});
}

export const GET = (event: RequestEvent) => proxy(event, 'GET');
export const POST = (event: RequestEvent) => proxy(event, 'POST');
export const PATCH = (event: RequestEvent) => proxy(event, 'PATCH');
export const PUT = (event: RequestEvent) => proxy(event, 'PUT');
export const DELETE = (event: RequestEvent) => proxy(event, 'DELETE');
