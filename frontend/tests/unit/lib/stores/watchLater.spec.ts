import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { PlaylistDetailOut } from '../../../../src/lib/types/api';

const { addWatchLater, removeWatchLater } = vi.hoisted(() => ({
	addWatchLater: vi.fn(),
	removeWatchLater: vi.fn()
}));

vi.mock('$lib/api', () => ({ api: { playlists: { addWatchLater, removeWatchLater } } }));

import { WatchLaterState } from '../../../../src/lib/stores/watchLater.svelte';

function detail(videoIds: string[] = []): PlaylistDetailOut {
	return {
		id: 'watch-later',
		name: 'Watch Later',
		description: null,
		thumbnail_url: null,
		is_system: true,
		system_key: 'watch_later',
		source_type: 'manual',
		source_channel_id: null,
		source_youtube_playlist_id: null,
		source_is_active: true,
		source_last_synced_at: null,
		current_position: null,
		total_videos: videoIds.length,
		created_at: '2026-07-14T00:00:00Z',
		video_ids: videoIds
	};
}

describe('WatchLaterState', () => {
	beforeEach(() => vi.clearAllMocks());

	it('persists an optimistic add and syncs the server response', async () => {
		const state = new WatchLaterState();
		state.sync(detail());
		addWatchLater.mockResolvedValue(detail(['video-1']));

		const request = state.setSaved('video-1', true);
		expect(state.isSaved('video-1')).toBe(true);
		await request;
		expect(addWatchLater).toHaveBeenCalledWith('video-1');
		expect(state.playlist?.total_videos).toBe(1);
	});

	it('rolls membership back when persistence fails', async () => {
		const state = new WatchLaterState();
		state.sync(detail(['video-1']));
		removeWatchLater.mockRejectedValue(new Error('offline'));

		await expect(state.setSaved('video-1', false)).rejects.toThrow('offline');
		expect(state.isSaved('video-1')).toBe(true);
		expect(state.isPending('video-1')).toBe(false);
	});
});
