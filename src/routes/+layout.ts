import { api } from '$lib/api';
import type { FolderOut, ChannelOut, TagOut } from '$lib/types/api';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ depends }) => {
	depends('app:folders');
	depends('app:channels');
	depends('app:tags');

	try {
		const [folders, tagsResponse] = await Promise.all([api.folders.getTree(), api.tags.list({ limit: 200 })]);
		const channels = [];

		let channelsResponse = await api.channels.list();
		do {
			for (const channel of channelsResponse.items) {
				channels.push(channel);
			}
			channelsResponse = await api.channels.list({
				limit: channelsResponse.limit,
				offset: channelsResponse.offset + channelsResponse.limit
			});
		} while (channelsResponse.has_more);
		const unfolderedChannels: ChannelOut[] = channels.filter(
			(channel) => channel.folder_id === null
		);
		return {
			folders,
			unfolderedChannels,
			channels,
			tags: tagsResponse.items
		};
	} catch (error) {
		console.error('Failed to load data:', error);
		// Return empty arrays on error to prevent layout from breaking
		return {
			folders: [] as FolderOut[],
			unfolderedChannels: [] as ChannelOut[],
			channels: [] as ChannelOut[],
			tags: [] as TagOut[]
		};
	}
};
