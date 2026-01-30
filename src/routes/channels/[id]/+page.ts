import { api } from '$lib/api';
import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	try {
		// Load channel details and videos in parallel
		const [channel, videosResponse] = await Promise.all([
			api.channels.get(params.id),
			api.videos.list({
				channel_id: params.id,
				limit: 100,
				offset: 0
			})
		]);

		return {
			channel,
			videos: videosResponse.items,
			total: videosResponse.total
		};
	} catch (err) {
		console.error('Failed to load channel:', err);
		throw error(404, 'Channel not found');
	}
};
