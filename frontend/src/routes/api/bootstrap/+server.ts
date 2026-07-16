import { json, type RequestHandler } from '@sveltejs/kit';
import { backendFetchFromEvent, refreshAuthSession } from '$lib/server/auth';

export const GET: RequestHandler = async (event) => {
	let response = await backendFetchFromEvent(event, '/app/bootstrap');

	if (response.status === 401 && (await refreshAuthSession(event))) {
		response = await backendFetchFromEvent(event, '/app/bootstrap');
	}

	const payload = await response.json().catch(() => ({ error: 'BOOTSTRAP_FAILED' }));
	return json(payload, { status: response.status });
};
