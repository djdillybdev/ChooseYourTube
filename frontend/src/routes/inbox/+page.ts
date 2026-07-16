import { api, APIError, createScopedAPI } from '$lib/api';
import { parseVideoFilterQuery } from '$lib/utils/videoFilterQuery';
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url, fetch, parent }) => {
	await parent();
	const scopedApi = createScopedAPI(fetch);
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const q = url.searchParams.get('q') || undefined;
	const offset = (page - 1) * pageSize;
	const { apiFilters } = parseVideoFilterQuery(url, { defaultWatched: false });

	try {
		// Invalidate video list cache to ensure fresh paginated results
		api.invalidate('videos/');

		const response = await scopedApi.videos.list({
			...apiFilters,
			q,
			limit: pageSize,
			offset
		});

		return {
			videos: response.items,
			total: response.total,
			page,
			pageSize,
			q
		};
	} catch (error) {
		if (error instanceof APIError && error.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}
		console.error('Failed to load inbox videos:', error);
		return {
			videos: [],
			total: 0,
			page: 1,
			pageSize,
			q,
			error: error instanceof Error ? error.message : 'Failed to load videos'
		};
	}
};
