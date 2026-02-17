import { api } from '$lib/api';
import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url }) => {
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const search = url.searchParams.get('search') || undefined;
	const offset = (page - 1) * pageSize;

	try {
		// Load channel details and videos in parallel
		const [channel, videosResponse] = await Promise.all([
			api.channels.get(params.id),
			api.videos.list({
				channel_id: params.id,
				search,
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
			search
		};
	} catch (err) {
		console.error('Failed to load channel:', err);
		throw error(404, 'Channel not found');
	}
};
