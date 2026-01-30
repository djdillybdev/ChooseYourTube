import { api } from '$lib/api';
import type { FolderOut, ChannelOut } from '$lib/types/api';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ depends }) => {
	depends('app:folders');
	depends('app:channels');

	try {
		const folders = await api.folders.getTree();
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
			unfolderedChannels
		};
	} catch (error) {
		console.error('Failed to load data:', error);
		// Return empty arrays on error to prevent layout from breaking
		return {
			folders: [] as FolderOut[],
			unfolderedChannels: [] as ChannelOut[]
		};
	}
};
