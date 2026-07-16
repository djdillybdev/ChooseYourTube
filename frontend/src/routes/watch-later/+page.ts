import { APIError, createScopedAPI } from '$lib/api';
import type { VideoOut } from '$lib/types/api';
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url, parent }) => {
	await parent();
	const api = createScopedAPI(fetch);
	try {
		const playlist = await api.playlists.getWatchLater();
		const byId = new Map<string, VideoOut>();
		const videos = await api.videos.listByIds(playlist.video_ids);
		for (const video of videos) byId.set(video.id, video);
		return {
			playlist,
			videos: playlist.video_ids
				.map((id) => byId.get(id))
				.filter((video): video is VideoOut => Boolean(video))
		};
	} catch (error) {
		if (error instanceof APIError && error.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname)}`);
		}
		throw error;
	}
};
