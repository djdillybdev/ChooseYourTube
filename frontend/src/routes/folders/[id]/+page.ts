import { APIError, createScopedAPI, type VideoOut } from '$lib/api';
import { parseVideoFilterQuery } from '$lib/utils/videoFilterQuery';
import { error, redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url, fetch, parent }) => {
	await parent();
	const api = createScopedAPI(fetch);
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const q = url.searchParams.get('q') || undefined;
	const offset = (page - 1) * pageSize;
	const { apiFilters } = parseVideoFilterQuery(url);

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
			let effectiveChannelIds = channelIds;
			if (apiFilters.channel_id) {
				const requestedChannelIds = apiFilters.channel_id
					.split(',')
					.map((id) => id.trim())
					.filter(Boolean);
				effectiveChannelIds = requestedChannelIds.filter((id) => channelIds.includes(id));
			}

			if (effectiveChannelIds.length === 0) {
				return {
					folder,
					channels: channelsResponse.items,
					videos: [] as VideoOut[],
					page,
					pageSize,
					total: 0,
					q
				};
			}

			videosResponse = await api.videos.list({
				...apiFilters,
				channel_id: effectiveChannelIds.join(','),
				q,
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
		if (err instanceof APIError && err.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}
		console.error('Failed to load folder:', err);
		throw error(404, 'Folder not found');
	}
};
