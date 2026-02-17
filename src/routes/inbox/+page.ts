import { api } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url }) => {
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const q = url.searchParams.get('q') || undefined;
	const offset = (page - 1) * pageSize;

	try {
		// Invalidate video list cache to ensure fresh paginated results
		api.invalidate('videos/');

		const response = await api.videos.list({
			is_watched: false,
			q,
			order_by: q ? 'relevance' : undefined,
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
