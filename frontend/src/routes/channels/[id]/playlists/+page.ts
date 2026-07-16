import { APIError, createScopedAPI } from '$lib/api';
import type { ChannelPlaylistOut } from '$lib/types/api';
import { error, redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

type ChannelPlaylistCard = ChannelPlaylistOut & {
	display_thumbnail_url: string | null;
};

async function resolvePlaylistCardThumbnail(
	api: ReturnType<typeof createScopedAPI>,
	playlist: ChannelPlaylistOut
): Promise<string | null> {
	if (playlist.thumbnail_url) {
		return playlist.thumbnail_url;
	}

	if (!playlist.total_videos) {
		return null;
	}

	const playlistDetail = await api.playlists.get(playlist.id);
	const firstVideoId = playlistDetail.video_ids[0];
	if (!firstVideoId) {
		return null;
	}

	const firstVideo = await api.videos.get(firstVideoId);
	return firstVideo.thumbnail_url ?? null;
}

export const load: PageLoad = async ({ params, url, fetch, parent }) => {
	await parent();
	const api = createScopedAPI(fetch);
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;
	const offset = (page - 1) * pageSize;

	try {
		const [channel, playlistsResponse] = await Promise.all([
			api.channels.get(params.id),
			api.channels.listPlaylists(params.id, {
				include_inactive: false,
				limit: pageSize,
				offset
			})
		]);

		const thumbnailResults = await Promise.allSettled(
			playlistsResponse.items.map((playlist) => resolvePlaylistCardThumbnail(api, playlist))
		);
		const firstAuthError = thumbnailResults.find(
			(result) =>
				result.status === 'rejected' &&
				result.reason instanceof APIError &&
				result.reason.status === 401
		);
		if (firstAuthError && firstAuthError.status === 'rejected') {
			throw firstAuthError.reason;
		}

		const playlists: ChannelPlaylistCard[] = playlistsResponse.items.map((playlist, index) => {
			const thumbnailResult = thumbnailResults[index];
			return {
				...playlist,
				display_thumbnail_url:
					thumbnailResult && thumbnailResult.status === 'fulfilled' ? thumbnailResult.value : null
			};
		});

		return {
			channel,
			playlists,
			total: playlistsResponse.total,
			page,
			pageSize
		};
	} catch (err) {
		if (err instanceof APIError && err.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}
		console.error('Failed to load channel playlists:', err);
		throw error(404, 'Channel not found');
	}
};
