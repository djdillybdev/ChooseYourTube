import { render, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import YouTubePlayer from '../../../../../src/lib/components/player/YouTubePlayer.svelte';
import type { VideoOut } from '../../../../../src/lib/types/api';

const { playNextMock, playerStateMock, updateVideoMock } = vi.hoisted(() => ({
	playNextMock: vi.fn().mockResolvedValue(undefined),
	playerStateMock: {
		current: {} as {
			currentVideo: VideoOut | null;
			queue: VideoOut[];
			isPlaying: boolean;
			volume: number;
		},
		update: vi.fn()
	},
	updateVideoMock: vi.fn()
}));

vi.mock('$lib/stores/playerState.svelte', () => ({
	playerState: playerStateMock,
	playNext: playNextMock
}));

vi.mock('$lib/api', () => ({
	api: {
		videos: {
			update: updateVideoMock
		}
	}
}));

let playerOptions: YT.PlayerOptions | undefined;
let playerTarget: YT.Player;

class MockPlayer {
	constructor(_element: string | HTMLElement, options: YT.PlayerOptions) {
		playerOptions = options;
		return playerTarget;
	}
}

function makeVideo(overrides: Partial<VideoOut> = {}): VideoOut {
	return {
		id: 'video-1',
		channel_id: 'channel-1',
		title: 'A video',
		description: null,
		thumbnail_url: null,
		published_at: '2026-01-01T00:00:00Z',
		created_at: '2026-01-01T00:00:00Z',
		duration_seconds: 120,
		is_watched: false,
		is_favorited: false,
		is_short: false,
		tag_ids: [],
		yt_tags: [],
		...overrides
	};
}

describe('YouTubePlayer', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		updateVideoMock.mockReset();
		playNextMock.mockReset().mockResolvedValue(undefined);
		playerStateMock.update.mockReset();
		playerOptions = undefined;

		const currentVideo = makeVideo();
		playerStateMock.current = {
			currentVideo,
			queue: [currentVideo, makeVideo({ id: 'video-2', title: 'Another video' })],
			isPlaying: false,
			volume: 75
		};
		playerStateMock.update.mockImplementation(
			(updater: (state: typeof playerStateMock.current) => typeof playerStateMock.current) => {
				playerStateMock.current = updater(playerStateMock.current);
			}
		);

		playerTarget = {
			loadVideoById: vi.fn(),
			playVideo: vi.fn(),
			pauseVideo: vi.fn(),
			stopVideo: vi.fn(),
			setVolume: vi.fn(),
			getVolume: vi.fn(),
			mute: vi.fn(),
			unMute: vi.fn(),
			destroy: vi.fn()
		} as unknown as YT.Player;

		vi.stubGlobal('YT', {
			Player: MockPlayer,
			PlayerState: {
				UNSTARTED: -1,
				ENDED: 0,
				PLAYING: 1,
				PAUSED: 2,
				BUFFERING: 3,
				CUED: 5
			}
		});
	});

	function emitState(data: number) {
		playerOptions?.events?.onStateChange?.({ target: playerTarget, data });
	}

	it('marks the current video as watched when playback starts and updates player state', async () => {
		const updatedVideo = makeVideo({ is_watched: true });
		updateVideoMock.mockResolvedValue(updatedVideo);
		render(YouTubePlayer);

		emitState(window.YT.PlayerState.PLAYING);

		await waitFor(() => {
			expect(updateVideoMock).toHaveBeenCalledWith('video-1', { is_watched: true });
		});
		expect(playerStateMock.current.currentVideo).toEqual(updatedVideo);
		expect(playerStateMock.current.queue).toEqual([
			updatedVideo,
			expect.objectContaining({ id: 'video-2', is_watched: false })
		]);
	});

	it('deduplicates repeated playback events while and after the update is pending', async () => {
		let resolveUpdate: (video: VideoOut) => void = () => undefined;
		updateVideoMock.mockReturnValue(
			new Promise<VideoOut>((resolve) => {
				resolveUpdate = resolve;
			})
		);
		render(YouTubePlayer);

		emitState(window.YT.PlayerState.PLAYING);
		emitState(window.YT.PlayerState.PLAYING);
		expect(updateVideoMock).toHaveBeenCalledOnce();

		resolveUpdate(makeVideo({ is_watched: true }));
		await waitFor(() => {
			expect(playerStateMock.current.currentVideo?.is_watched).toBe(true);
		});
		emitState(window.YT.PlayerState.PLAYING);

		expect(updateVideoMock).toHaveBeenCalledOnce();
	});

	it('does not update a video that is already watched', () => {
		const watchedVideo = makeVideo({ is_watched: true });
		playerStateMock.current = {
			...playerStateMock.current,
			currentVideo: watchedVideo,
			queue: [watchedVideo]
		};
		render(YouTubePlayer);

		emitState(window.YT.PlayerState.PLAYING);

		expect(updateVideoMock).not.toHaveBeenCalled();
	});

	it('keeps playback running and retries after a watched update fails', async () => {
		vi.spyOn(console, 'error').mockImplementation(() => undefined);
		updateVideoMock
			.mockRejectedValueOnce(new Error('Network unavailable'))
			.mockResolvedValueOnce(makeVideo({ is_watched: true }));
		render(YouTubePlayer);

		emitState(window.YT.PlayerState.PLAYING);
		await waitFor(() => {
			expect(console.error).toHaveBeenCalledWith(
				'Failed to mark video as watched:',
				expect.any(Error)
			);
		});
		expect(playerStateMock.current.isPlaying).toBe(true);
		expect(playNextMock).not.toHaveBeenCalled();

		emitState(window.YT.PlayerState.PLAYING);
		await waitFor(() => expect(updateVideoMock).toHaveBeenCalledTimes(2));
	});

	it('advances the queue once when playback ends', async () => {
		render(YouTubePlayer);

		emitState(window.YT.PlayerState.ENDED);
		emitState(window.YT.PlayerState.ENDED);

		expect(playNextMock).toHaveBeenCalledOnce();
		expect(updateVideoMock).not.toHaveBeenCalled();
	});
});
