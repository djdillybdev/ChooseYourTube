import { api } from '$lib/api';
import { parseVideoFilterQuery } from '$lib/utils/videoFilterQuery';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url }) => {
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const q = url.searchParams.get('q') || undefined;
	const offset = (page - 1) * pageSize;
	const { apiFilters } = parseVideoFilterQuery(url, { defaultWatched: false });

	try {
		// Invalidate video list cache to ensure fresh paginated results
		api.invalidate('videos/');

		const response = await api.videos.list({
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
