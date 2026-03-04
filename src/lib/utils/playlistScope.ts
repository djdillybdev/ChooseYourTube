import type { PlaylistOut } from '$lib/types/api';

/**
 * Manual playlists are user-managed lists (not system queue and not channel-synced playlists).
 */
export function isManualPlaylist(playlist: PlaylistOut): boolean {
	return !playlist.is_system && playlist.source_channel_id === null;
}
