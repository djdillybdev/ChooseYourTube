import { APIError, createScopedAPI } from '$lib/api';
import type { VideoOut } from '$lib/types/api';
import { error, redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

async function hydratePlaylistVideos(api: ReturnType<typeof createScopedAPI>, videoIds: string[]) {
	if (!videoIds.length) return [] as VideoOut[];

	const byId = new Map<string, VideoOut>();
	const results = await Promise.allSettled(videoIds.map((id) => api.videos.get(id)));

	for (const result of results) {
		if (result.status === 'fulfilled') {
			byId.set(result.value.id, result.value);
		}
	}

	return videoIds.map((id) => byId.get(id)).filter((video): video is VideoOut => Boolean(video));
}

export const load: PageLoad = async ({ params, url, fetch }) => {
	const api = createScopedAPI(fetch);
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const offset = (page - 1) * pageSize;

	try {
		const [channel, playlist] = await Promise.all([
			api.channels.get(params.id),
			api.playlists.get(params.playlistId)
		]);

		if (playlist.source_channel_id && playlist.source_channel_id !== params.id) {
			throw error(404, 'Playlist not found');
		}

		const pagedIds = playlist.video_ids.slice(offset, offset + pageSize);
		const videos = await hydratePlaylistVideos(api, pagedIds);

		return {
			channel,
			playlist,
			videos,
			total: playlist.total_videos,
			page,
			pageSize
		};
	} catch (err) {
		if (err instanceof APIError && err.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}
		console.error('Failed to load playlist videos:', err);
		throw error(404, 'Playlist not found');
	}
};
