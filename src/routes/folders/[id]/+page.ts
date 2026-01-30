import { api, type VideoOut } from '$lib/api';
import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	try {
		// Load folder details
		const folder = await api.folders.get(parseInt(params.id));

		// Load channels in this folder
		const channelsResponse = await api.channels.list({
			folder_id: parseInt(params.id),
			limit: 100
		});

		// Load videos from channels in this folder
		// Note: The API doesn't have a direct folder filter for videos,
		// so we need to get videos by channel_ids
		const channelIds = channelsResponse.items.map((ch) => ch.id);

		let allVideos: VideoOut[] = [];
		if (channelIds.length > 0) {
			const videosResponse = await api.videos.list({
				channel_id: channelIds.join(','),
				limit: 100,
				offset: 0
			});

			allVideos = videosResponse.items;
		}

		return {
			folder,
			channels: channelsResponse.items,
			videos: allVideos
		};
	} catch (err) {
		console.error('Failed to load folder:', err);
		throw error(404, 'Folder not found');
	}
};
