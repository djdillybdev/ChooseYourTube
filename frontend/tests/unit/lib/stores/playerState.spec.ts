import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { PlaylistDetailOut, VideoOut } from '../../../../src/lib/types/api';
import { clearQueue, playerState } from '../../../../src/lib/stores/playerState.svelte';

const {
	clearQueueVideosMock,
	hydrateQueueVideosMock,
	loadQueueDetailMock,
	replaceQueueVideosMock
} = vi.hoisted(() => ({
	clearQueueVideosMock: vi.fn(),
	hydrateQueueVideosMock: vi.fn(),
	loadQueueDetailMock: vi.fn(),
	replaceQueueVideosMock: vi.fn()
}));

vi.mock('$lib/services/queuePlaylist', () => ({
	addVideoToQueue: vi.fn(),
	clearQueueVideos: clearQueueVideosMock,
	ensureQueuePlaylist: vi.fn(),
	hydrateQueueVideos: hydrateQueueVideosMock,
	loadQueueDetail: loadQueueDetailMock,
	moveQueueVideo: vi.fn(),
	replaceQueueVideos: replaceQueueVideosMock,
	removeVideoFromQueue: vi.fn(),
	setQueuePosition: vi.fn()
}));

function makeVideo(id: string): VideoOut {
	return {
		id,
		channel_id: 'channel-1',
		title: `Video ${id}`,
		description: null,
		thumbnail_url: null,
		published_at: '2026-01-01T00:00:00Z',
		created_at: '2026-01-01T00:00:00Z',
		duration_seconds: 120,
		is_watched: false,
		is_favorited: false,
		is_short: false,
		tag_ids: [],
		yt_tags: []
	};
}

function detail(videoIds: string[], currentPosition: number | null): PlaylistDetailOut {
	return {
		id: 'queue-id',
		name: 'Queue',
		description: null,
		thumbnail_url: null,
		is_system: true,
		system_key: null,
		source_type: 'manual',
		source_channel_id: null,
		source_youtube_playlist_id: null,
		source_is_active: false,
		source_last_synced_at: null,
		current_position: currentPosition,
		total_videos: videoIds.length,
		created_at: '2026-01-01T00:00:00Z',
		video_ids: videoIds
	};
}

describe('clearQueue', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('keeps the current video and playback active', async () => {
		const current = makeVideo('current');
		const other = makeVideo('other');
		playerState.current = {
			...playerState.current,
			currentVideo: current,
			queue: [other, current],
			queueIndex: 1,
			queuePlaylistId: 'queue-id',
			queueMode: 'system',
			queueMutable: true,
			isQueueReady: true,
			isPlaying: true
		};
		replaceQueueVideosMock.mockResolvedValue(detail(['current'], 0));
		loadQueueDetailMock.mockResolvedValue(detail(['current'], 0));
		hydrateQueueVideosMock.mockResolvedValue([current]);

		await clearQueue();

		expect(replaceQueueVideosMock).toHaveBeenCalledWith('queue-id', ['current']);
		expect(clearQueueVideosMock).not.toHaveBeenCalled();
		expect(playerState.current.currentVideo).toEqual(current);
		expect(playerState.current.queue).toEqual([current]);
		expect(playerState.current.queueIndex).toBe(0);
		expect(playerState.current.isPlaying).toBe(true);
	});

	it('empties a queue that has no current video', async () => {
		playerState.current = {
			...playerState.current,
			currentVideo: null,
			queue: [makeVideo('waiting')],
			queueIndex: 0,
			queuePlaylistId: 'queue-id',
			queueMode: 'system',
			queueMutable: true,
			isQueueReady: true,
			isPlaying: false
		};
		clearQueueVideosMock.mockResolvedValue(detail([], null));
		loadQueueDetailMock.mockResolvedValue(detail([], null));
		hydrateQueueVideosMock.mockResolvedValue([]);

		await clearQueue();

		expect(clearQueueVideosMock).toHaveBeenCalledWith('queue-id');
		expect(replaceQueueVideosMock).not.toHaveBeenCalled();
		expect(playerState.current.queue).toEqual([]);
		expect(playerState.current.currentVideo).toBeNull();
	});
});
