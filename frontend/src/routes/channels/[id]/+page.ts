import { APIError, createScopedAPI } from '$lib/api';
import { parseVideoFilterQuery } from '$lib/utils/videoFilterQuery';
import { error, redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url, fetch, parent }) => {
	await parent();
	const api = createScopedAPI(fetch);
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const q = url.searchParams.get('q') || undefined;
	const offset = (page - 1) * pageSize;
	const { apiFilters } = parseVideoFilterQuery(url, { forcedChannelId: params.id });

	try {
		// Load channel details and videos in parallel
		const [channel, videosResponse] = await Promise.all([
			api.channels.get(params.id),
			api.videos.list({
				...apiFilters,
				q,
				limit: pageSize,
				offset
			})
		]);

		return {
			channel,
			videos: videosResponse.items,
			total: videosResponse.total,
			page,
			pageSize,
			q
		};
	} catch (err) {
		if (err instanceof APIError && err.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}
		console.error('Failed to load channel:', err);
		throw error(404, 'Channel not found');
	}
};
