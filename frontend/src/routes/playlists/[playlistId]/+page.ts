import { APIError, createScopedAPI } from '$lib/api';
import type { VideoOut } from '$lib/types/api';
import { isManualPlaylist } from '$lib/utils/playlistScope';
import { error, redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

async function hydratePlaylistVideos(api: ReturnType<typeof createScopedAPI>, videoIds: string[]) {
	if (!videoIds.length) return [] as VideoOut[];

	const byId = new Map<string, VideoOut>();
	const videos = await api.videos.listByIds(videoIds);
	for (const video of videos) byId.set(video.id, video);

	return videoIds.map((id) => byId.get(id)).filter((video): video is VideoOut => Boolean(video));
}

export const load: PageLoad = async ({ params, url, fetch, parent }) => {
	await parent();
	const api = createScopedAPI(fetch);

	try {
		const playlist = await api.playlists.get(params.playlistId);
		if (!isManualPlaylist(playlist)) {
			throw error(404, 'Playlist not found');
		}

		const videos = await hydratePlaylistVideos(api, playlist.video_ids);

		return {
			playlist,
			videos
		};
	} catch (err) {
		if (err instanceof APIError && err.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}

		if ((err as { status?: number })?.status === 404) {
			throw err;
		}

		console.error('Failed to load playlist:', err);
		throw error(404, 'Playlist not found');
	}
};
