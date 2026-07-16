import { APIError, createScopedAPI } from '$lib/api';
import type { PlaylistOut } from '$lib/types/api';
import { isManualPlaylist } from '$lib/utils/playlistScope';
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

type PlaylistCard = PlaylistOut & {
	total_videos: number;
	display_thumbnail_url: string | null;
};

async function listAllNonSystemPlaylists(
	api: ReturnType<typeof createScopedAPI>
): Promise<PlaylistOut[]> {
	const playlists: PlaylistOut[] = [];
	let response = await api.playlists.list({ is_system: false, limit: 200, offset: 0 });

	do {
		playlists.push(...response.items);
		if (!response.has_more) break;
		response = await api.playlists.list({
			is_system: false,
			limit: response.limit,
			offset: response.offset + response.limit
		});
	} while (response.has_more);

	return playlists;
}

export const load: PageLoad = async ({ url, fetch, parent }) => {
	await parent();
	const api = createScopedAPI(fetch);
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = Number(url.searchParams.get('pageSize')) || 24;

	try {
		const allPlaylists = await listAllNonSystemPlaylists(api);
		const manualPlaylists = allPlaylists.filter(isManualPlaylist);
		const total = manualPlaylists.length;
		const offset = (page - 1) * pageSize;
		const pagedPlaylists = manualPlaylists.slice(offset, offset + pageSize);

		const cards = pagedPlaylists.map(
			(playlist): PlaylistCard => ({
				...playlist,
				total_videos: playlist.total_videos,
				display_thumbnail_url: playlist.preview_thumbnail_url ?? null
			})
		);

		return {
			playlists: cards,
			total,
			page,
			pageSize
		};
	} catch (err) {
		if (err instanceof APIError && err.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}

		console.error('Failed to load playlists:', err);
		return {
			playlists: [] as PlaylistCard[],
			total: 0,
			page,
			pageSize,
			error: err instanceof Error ? err.message : 'Failed to load playlists'
		};
	}
};
