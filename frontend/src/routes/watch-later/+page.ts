import { APIError, createScopedAPI } from '$lib/api';
import type { VideoOut } from '$lib/types/api';
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = createScopedAPI(fetch);
	try {
		const playlist = await api.playlists.getWatchLater();
		const results = await Promise.allSettled(playlist.video_ids.map((id) => api.videos.get(id)));
		const byId = new Map<string, VideoOut>();
		for (const result of results) {
			if (result.status === 'fulfilled') byId.set(result.value.id, result.value);
		}
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
