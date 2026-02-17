import { api, type VideoOut } from '$lib/api';
import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url }) => {
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const q = url.searchParams.get('q') || undefined;
	const offset = (page - 1) * pageSize;

	try {
		// Load folder details
		const folder = await api.folders.get(params.id);

		// Load channels in this folder (no pagination, use high limit)
		const channelsResponse = await api.channels.list({
			folder_id: params.id,
			limit: 100
		});

		// Load videos from channels in this folder
		// Note: The API doesn't have a direct folder filter for videos,
		// so we need to get videos by channel_ids
		const channelIds = channelsResponse.items.map((ch) => ch.id);

		let videosResponse = { items: [] as VideoOut[], total: 0 };
		if (channelIds.length > 0) {
			videosResponse = await api.videos.list({
				channel_id: channelIds.join(','),
				q,
				order_by: q ? 'relevance' : undefined,
				limit: pageSize,
				offset
			});
		}

		return {
			folder,
			channels: channelsResponse.items,
			videos: videosResponse.items,
			page,
			pageSize,
			total: videosResponse.total,
			q
		};
	} catch (err) {
		console.error('Failed to load folder:', err);
		throw error(404, 'Folder not found');
	}
};
