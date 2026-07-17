import type { VideoOut } from '$lib/types/api';
import {
	addVideoToQueue,
	clearQueueVideos,
	ensureQueuePlaylist,
	hydrateQueueVideos,
	loadQueueDetail,
	moveQueueVideo,
	replaceQueueVideos,
	removeVideoFromQueue,
	setQueuePosition
} from '$lib/services/queuePlaylist';

/**
 * Player size options
 */
export type PlayerSize = 'mini' | 'compact' | 'expanded';

/**
 * Repeat mode options
 */
export type RepeatMode = 'none' | 'one' | 'all';

/**
 * Player state interface
 */
interface PlayerState {
	currentVideo: VideoOut | null;
	queue: VideoOut[];
	queueIndex: number;
	queuePlaylistId: string | null;
	queueMode: 'system' | 'playlist';
	queueMutable: boolean;
	activeSourcePlaylistId: string | null;
	isQueueReady: boolean;
	isQueueSyncing: boolean;
	queueError: string | null;
	isPlaying: boolean;
	volume: number;
	playerSize: PlayerSize;
	repeatMode: RepeatMode;
	shuffleEnabled: boolean;
}

interface PersistedPlayerState {
	volume?: number;
	playerSize?: PlayerSize;
	repeatMode?: RepeatMode;
	shuffleEnabled?: boolean;
}

/**
 * Default player state
 */
const defaultState: PlayerState = {
	currentVideo: null,
	queue: [],
	queueIndex: 0,
	queuePlaylistId: null,
	queueMode: 'system',
	queueMutable: true,
	activeSourcePlaylistId: null,
	isQueueReady: false,
	isQueueSyncing: false,
	queueError: null,
	isPlaying: false,
	volume: 75,
	playerSize: 'compact',
	repeatMode: 'none',
	shuffleEnabled: false
};

/**
 * Load state from localStorage (preferences only)
 */
function loadState(): PlayerState {
	if (typeof window === 'undefined') return defaultState;

	try {
		const stored = localStorage.getItem('cyt:player');
		if (!stored) return defaultState;

		const parsed = JSON.parse(stored) as PersistedPlayerState;
		return {
			...defaultState,
			volume: parsed.volume ?? defaultState.volume,
			playerSize: parsed.playerSize ?? defaultState.playerSize,
			repeatMode: parsed.repeatMode ?? defaultState.repeatMode,
			shuffleEnabled: parsed.shuffleEnabled ?? defaultState.shuffleEnabled
		};
	} catch {
		return defaultState;
	}
}

/**
 * Save state to localStorage (preferences only)
 */
function saveState(state: PlayerState) {
	if (typeof window === 'undefined') return;

	try {
		const persisted: PersistedPlayerState = {
			volume: state.volume,
			playerSize: state.playerSize,
			repeatMode: state.repeatMode,
			shuffleEnabled: state.shuffleEnabled
		};
		localStorage.setItem('cyt:player', JSON.stringify(persisted));
	} catch (error) {
		console.error('Failed to save player state:', error);
	}
}

/**
 * Create reactive player state
 */
function createPlayerState() {
	let state = $state<PlayerState>(loadState());

	return {
		get current() {
			return state;
		},
		set current(value: PlayerState) {
			state = value;
			saveState(state);
		},
		update(fn: (state: PlayerState) => PlayerState) {
			state = fn(state);
			saveState(state);
		}
	};
}

export const playerState = createPlayerState();

let queueInitPromise: Promise<void> | null = null;
let queueMutationChain: Promise<void> = Promise.resolve();

function normalizeQueueState(
	state: PlayerState,
	queue: VideoOut[],
	position: number | null
): PlayerState {
	if (position === null || position < 0 || position >= queue.length) {
		return {
			...state,
			queue,
			queueIndex: 0,
			currentVideo: null
		};
	}

	return {
		...state,
		queue,
		queueIndex: position,
		currentVideo: queue[position] ?? null
	};
}

function setQueueError(error: unknown) {
	playerState.update((state) => ({
		...state,
		queueError: error instanceof Error ? error.message : 'Queue operation failed'
	}));
}

function runQueuedMutation<T>(mutation: () => Promise<T>): Promise<T> {
	const task = queueMutationChain.then(mutation, mutation);
	queueMutationChain = task.then(
		() => undefined,
		() => undefined
	);
	return task;
}

async function syncFromPlaylistDetail(
	playlistId: string,
	options: {
		setPlaying?: boolean;
		clearError?: boolean;
		queueMode?: 'system' | 'playlist';
		queueMutable?: boolean;
		activeSourcePlaylistId?: string | null;
	} = {}
) {
	const detail = await loadQueueDetail(playlistId);
	const queue = await hydrateQueueVideos(detail.video_ids);

	playerState.update((state) => {
		const normalized = normalizeQueueState(state, queue, detail.current_position);
		return {
			...normalized,
			queuePlaylistId: playlistId,
			queueMode: options.queueMode ?? state.queueMode,
			queueMutable: options.queueMutable ?? state.queueMutable,
			activeSourcePlaylistId: options.activeSourcePlaylistId ?? state.activeSourcePlaylistId,
			isQueueReady: true,
			isQueueSyncing: false,
			queueError: options.clearError ? null : state.queueError,
			isPlaying: options.setPlaying ?? state.isPlaying
		};
	});
}

/**
 * Ensure queue playlist exists and load queue state.
 */
export async function initializeQueue(force = false): Promise<void> {
	if (!force && playerState.current.isQueueReady) {
		return;
	}

	if (!force && queueInitPromise) {
		return queueInitPromise;
	}

	queueInitPromise = (async () => {
		playerState.update((state) => ({
			...state,
			isQueueSyncing: true,
			queueError: null
		}));

		try {
			const playlist = await ensureQueuePlaylist();
			await syncFromPlaylistDetail(playlist.id, {
				clearError: true,
				queueMode: 'system',
				queueMutable: true,
				activeSourcePlaylistId: null
			});
		} catch (error) {
			setQueueError(error);
			playerState.update((state) => ({
				...state,
				isQueueReady: false,
				isQueueSyncing: false
			}));
		}
	})();

	try {
		await queueInitPromise;
	} finally {
		queueInitPromise = null;
	}
}

/**
 * Play a video. If it is not already queued, insert it next.
 */
export async function playVideo(video: VideoOut): Promise<boolean> {
	await initializeQueue(playerState.current.queueMode === 'playlist');
	const playlistId = playerState.current.queuePlaylistId;
	if (!playlistId) return false;

	let succeeded = false;
	await runQueuedMutation(async () => {
		playerState.update((state) => ({ ...state, isQueueSyncing: true, queueError: null }));

		try {
			const currentState = playerState.current;
			const existingIndex = currentState.queue.findIndex((v) => v.id === video.id);

			if (existingIndex >= 0) {
				await setQueuePosition(playlistId, existingIndex);
				await syncFromPlaylistDetail(playlistId, { setPlaying: true, clearError: true });
				succeeded = true;
				return;
			}

			const insertPosition =
				currentState.queue.length === 0
					? 0
					: Math.min(currentState.queueIndex + 1, currentState.queue.length);

			await addVideoToQueue(playlistId, video.id, insertPosition);
			await setQueuePosition(playlistId, insertPosition);
			await syncFromPlaylistDetail(playlistId, { setPlaying: true, clearError: true });
			succeeded = true;
		} catch (error) {
			setQueueError(error);
			playerState.update((state) => ({ ...state, isQueueSyncing: false }));
		}
	});
	return succeeded;
}

/**
 * Play from an existing playlist using the playlist order as queue.
 * Queue content/order are read-only in this mode.
 */
export async function playFromPlaylist(playlistId: string, videoId: string): Promise<boolean> {
	let succeeded = false;
	await runQueuedMutation(async () => {
		playerState.update((state) => ({ ...state, isQueueSyncing: true, queueError: null }));

		try {
			const detail = await loadQueueDetail(playlistId);
			const startPosition = detail.video_ids.indexOf(videoId);
			if (startPosition < 0) {
				throw new Error('Video not found in playlist');
			}

			await setQueuePosition(playlistId, startPosition);
			await syncFromPlaylistDetail(playlistId, {
				setPlaying: true,
				clearError: true,
				queueMode: 'playlist',
				queueMutable: false,
				activeSourcePlaylistId: playlistId
			});
			succeeded = true;
		} catch (error) {
			setQueueError(error);
			playerState.update((state) => ({ ...state, isQueueSyncing: false }));
		}
	});
	return succeeded;
}

/**
 * Add video to queue without starting playback.
 */
export async function addToQueue(video: VideoOut, position: 'next' | 'end' = 'end'): Promise<void> {
	await initializeQueue();
	if (!playerState.current.queueMutable) return;
	const playlistId = playerState.current.queuePlaylistId;
	if (!playlistId) return;

	await runQueuedMutation(async () => {
		playerState.update((state) => ({ ...state, isQueueSyncing: true, queueError: null }));

		try {
			const currentState = playerState.current;
			const existingIndex = currentState.queue.findIndex((v) => v.id === video.id);
			if (existingIndex >= 0) {
				playerState.update((state) => ({ ...state, isQueueSyncing: false }));
				return;
			}

			const insertPosition =
				position === 'next'
					? currentState.queue.length === 0
						? 0
						: Math.min(currentState.queueIndex + 1, currentState.queue.length)
					: undefined;

			await addVideoToQueue(playlistId, video.id, insertPosition);
			await syncFromPlaylistDetail(playlistId, { clearError: true });
		} catch (error) {
			setQueueError(error);
			playerState.update((state) => ({ ...state, isQueueSyncing: false }));
		}
	});
}

/**
 * Remove a video from queue.
 */
export async function removeFromQueue(videoId: string): Promise<void> {
	await initializeQueue();
	if (!playerState.current.queueMutable) return;
	const playlistId = playerState.current.queuePlaylistId;
	if (!playlistId) return;

	await runQueuedMutation(async () => {
		playerState.update((state) => ({ ...state, isQueueSyncing: true, queueError: null }));

		try {
			await removeVideoFromQueue(playlistId, videoId);
			await syncFromPlaylistDetail(playlistId, { clearError: true });
		} catch (error) {
			setQueueError(error);
			playerState.update((state) => ({ ...state, isQueueSyncing: false }));
		}
	});
}

/**
 * Move a queue item to a new position.
 */
export async function moveQueueItem(videoId: string, newPosition: number): Promise<void> {
	await initializeQueue();
	if (!playerState.current.queueMutable) return;
	const playlistId = playerState.current.queuePlaylistId;
	if (!playlistId) return;

	await runQueuedMutation(async () => {
		playerState.update((state) => ({ ...state, isQueueSyncing: true, queueError: null }));

		try {
			await moveQueueVideo(playlistId, videoId, newPosition);
			await syncFromPlaylistDetail(playlistId, { clearError: true });
		} catch (error) {
			setQueueError(error);
			playerState.update((state) => ({ ...state, isQueueSyncing: false }));
		}
	});
}

/**
 * Play next video in queue.
 */
export async function playNext(): Promise<void> {
	await initializeQueue();
	const playlistId = playerState.current.queuePlaylistId;
	if (!playlistId) return;

	await runQueuedMutation(async () => {
		const state = playerState.current;
		if (!state.queue.length) {
			playerState.update((s) => ({ ...s, isPlaying: false }));
			return;
		}

		if (state.repeatMode === 'one' && state.queueIndex < state.queue.length) {
			playerState.update((s) => ({ ...s, isPlaying: true }));
			return;
		}

		const nextIndex = state.queueIndex + 1;
		if (nextIndex < state.queue.length) {
			try {
				playerState.update((s) => ({ ...s, isQueueSyncing: true, queueError: null }));
				await setQueuePosition(playlistId, nextIndex);
				await syncFromPlaylistDetail(playlistId, { setPlaying: true, clearError: true });
			} catch (error) {
				setQueueError(error);
				playerState.update((s) => ({ ...s, isQueueSyncing: false }));
			}
			return;
		}

		if (state.repeatMode === 'all') {
			try {
				playerState.update((s) => ({ ...s, isQueueSyncing: true, queueError: null }));
				await setQueuePosition(playlistId, 0);
				await syncFromPlaylistDetail(playlistId, { setPlaying: true, clearError: true });
			} catch (error) {
				setQueueError(error);
				playerState.update((s) => ({ ...s, isQueueSyncing: false }));
			}
			return;
		}

		playerState.update((s) => ({ ...s, isPlaying: false }));
	});
}

/**
 * Play previous video in queue.
 */
export async function playPrevious(): Promise<void> {
	await initializeQueue();
	const playlistId = playerState.current.queuePlaylistId;
	if (!playlistId) return;

	await runQueuedMutation(async () => {
		const state = playerState.current;
		if (state.queueIndex <= 0) return;

		playerState.update((s) => ({ ...s, isQueueSyncing: true, queueError: null }));
		try {
			await setQueuePosition(playlistId, state.queueIndex - 1);
			await syncFromPlaylistDetail(playlistId, { setPlaying: true, clearError: true });
		} catch (error) {
			setQueueError(error);
			playerState.update((s) => ({ ...s, isQueueSyncing: false }));
		}
	});
}

/**
 * Jump to specific video in queue.
 */
export async function jumpToQueueItem(index: number): Promise<boolean> {
	await initializeQueue();
	const playlistId = playerState.current.queuePlaylistId;
	if (!playlistId) return false;
	if (index < 0 || index >= playerState.current.queue.length) return false;

	let succeeded = false;
	await runQueuedMutation(async () => {
		playerState.update((state) => ({ ...state, isQueueSyncing: true, queueError: null }));
		try {
			await setQueuePosition(playlistId, index);
			await syncFromPlaylistDetail(playlistId, { setPlaying: true, clearError: true });
			succeeded = true;
		} catch (error) {
			setQueueError(error);
			playerState.update((state) => ({ ...state, isQueueSyncing: false }));
		}
	});
	return succeeded;
}

/**
 * Clear queued videos while preserving the current video and playback.
 */
export async function clearQueue(): Promise<void> {
	await initializeQueue();
	if (!playerState.current.queueMutable) return;
	const playlistId = playerState.current.queuePlaylistId;
	if (!playlistId) return;

	await runQueuedMutation(async () => {
		playerState.update((state) => ({ ...state, isQueueSyncing: true, queueError: null }));
		try {
			const currentVideo = playerState.current.currentVideo;
			if (currentVideo) {
				await replaceQueueVideos(playlistId, [currentVideo.id]);
			} else {
				await clearQueueVideos(playlistId);
			}
			await syncFromPlaylistDetail(playlistId, { clearError: true });
		} catch (error) {
			setQueueError(error);
			playerState.update((state) => ({ ...state, isQueueSyncing: false }));
		}
	});
}

/**
 * Toggle play/pause.
 */
export function togglePlayPause() {
	playerState.update((state) => ({
		...state,
		isPlaying: state.currentVideo ? !state.isPlaying : false
	}));
}

/**
 * Set volume (0-100).
 */
export function setVolume(volume: number) {
	playerState.update((state) => ({
		...state,
		volume: Math.max(0, Math.min(100, volume))
	}));
}

/**
 * Set player size.
 */
export function setPlayerSize(size: PlayerSize) {
	playerState.update((state) => ({
		...state,
		playerSize: size
	}));
}

/**
 * Cycle repeat mode.
 */
export function cycleRepeatMode() {
	playerState.update((state) => {
		const modes: RepeatMode[] = ['none', 'one', 'all'];
		const currentIndex = modes.indexOf(state.repeatMode);
		const nextMode = modes[(currentIndex + 1) % modes.length];

		return {
			...state,
			repeatMode: nextMode
		};
	});
}

/**
 * Toggle shuffle mode.
 */
export function toggleShuffle() {
	playerState.update((state) => ({
		...state,
		shuffleEnabled: !state.shuffleEnabled
	}));
}

/**
 * Close player (stop playback and clear current video).
 */
export async function closePlayer() {
	const playlistId = playerState.current.queuePlaylistId;
	playerState.update((state) => ({
		...state,
		currentVideo: null,
		isPlaying: false
	}));

	if (!playlistId) return;

	try {
		await setQueuePosition(playlistId, null);
	} catch (error) {
		setQueueError(error);
	}
}
