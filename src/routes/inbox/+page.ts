import { api } from '$lib/api';

export async function load() {
	try {
		// Load unwatched videos (default filter)
		const response = await api.videos.list({
			is_watched: false,
			limit: 50,
			offset: 0
		});

		return {
			videos: response.items,
			total: response.total,
			hasMore: response.has_more
		};
	} catch (error) {
		console.error('Failed to load inbox videos:', error);
		return {
			videos: [],
			total: 0,
			hasMore: false,
			error: error instanceof Error ? error.message : 'Failed to load videos'
		};
	}
}
