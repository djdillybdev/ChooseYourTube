import { APIError, createScopedAPI, type VideoOut } from '$lib/api';
import { parseVideoFilterQuery } from '$lib/utils/videoFilterQuery';
import { error, redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url, fetch, parent }) => {
	const layout = await parent();
	const category = layout.categories.find((item) => item.id === params.id);
	if (!category) throw error(404, 'Category not found');

	const channelIds = new Set(category.channel_ids ?? []);
	const channels = layout.channels.filter((channel) => channelIds.has(channel.id));
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const q = url.searchParams.get('q') || undefined;
	const offset = (page - 1) * pageSize;
	const { apiFilters } = parseVideoFilterQuery(url);

	try {
		let videosResponse = { items: [] as VideoOut[], total: 0 };
		if (channels.length > 0) {
			let effectiveChannelIds = channels.map((channel) => channel.id);
			if (apiFilters.channel_id) {
				const requested = apiFilters.channel_id
					.split(',')
					.map((id) => id.trim())
					.filter(Boolean);
				effectiveChannelIds = requested.filter((id) => channelIds.has(id));
			}
			if (effectiveChannelIds.length > 0) {
				videosResponse = await createScopedAPI(fetch).videos.list({
					...apiFilters,
					channel_id: effectiveChannelIds.join(','),
					q,
					limit: pageSize,
					offset
				});
			}
		}

		return {
			category,
			channels,
			videos: videosResponse.items,
			page,
			pageSize,
			total: videosResponse.total,
			q
		};
	} catch (cause) {
		if (cause instanceof APIError && cause.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}
		console.error('Failed to load category:', cause);
		throw error(502, 'Category videos could not be loaded. Please retry.');
	}
};
