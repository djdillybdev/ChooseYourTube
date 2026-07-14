import { json, type RequestHandler } from '@sveltejs/kit';
import { backendFetch } from '$lib/server/auth';

export const GET: RequestHandler = async () => {
	try {
		const response = await backendFetch({ path: '/' });
		if (!response.ok) {
			return json({ code: 'METADATA_UNAVAILABLE' }, { status: 503 });
		}
		return new Response(response.body, {
			status: 200,
			headers: { 'Content-Type': 'application/json' }
		});
	} catch {
		return json({ code: 'METADATA_UNAVAILABLE' }, { status: 503 });
	}
};
