import type { VideoOut } from '$lib/types/api';

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
	isPlaying: boolean;
	volume: number;
	playerSize: PlayerSize;
	repeatMode: RepeatMode;
	shuffleEnabled: boolean;
}

/**
 * Default player state
 */
const defaultState: PlayerState = {
	currentVideo: null,
	queue: [],
	queueIndex: 0,
	isPlaying: false,
	volume: 75,
	playerSize: 'compact',
	repeatMode: 'none',
	shuffleEnabled: false
};

/**
 * Load state from localStorage
 */
function loadState(): PlayerState {
	if (typeof window === 'undefined') return defaultState;

	try {
		const stored = localStorage.getItem('cyt:player');
		return stored ? { ...defaultState, ...JSON.parse(stored) } : defaultState;
	} catch {
		return defaultState;
	}
}

/**
 * Save state to localStorage
 */
function saveState(state: PlayerState) {
	if (typeof window === 'undefined') return;

	try {
		localStorage.setItem('cyt:player', JSON.stringify(state));
	} catch (error) {
		console.error('Failed to save player state:', error);
	}
}

/**
 * Create reactive player state
 */
function createPlayerState() {
	let state = $state<PlayerState>(loadState());

	// Auto-save to localStorage on changes
	$effect(() => {
		saveState(state);
	});

	return {
		get current() {
			return state;
		},
		set current(value: PlayerState) {
			state = value;
		},
		update(fn: (state: PlayerState) => PlayerState) {
			state = fn(state);
		}
	};
}

export const playerState = createPlayerState();

/**
 * Play a video (sets as current and starts playback)
 */
export function playVideo(video: VideoOut) {
	playerState.update((state) => {
		// Check if video is already in queue
		const existingIndex = state.queue.findIndex((v) => v.id === video.id);

		if (existingIndex >= 0) {
			// Video is in queue, jump to it
			return {
				...state,
				currentVideo: video,
				isPlaying: true,
				queueIndex: existingIndex
			};
		} else {
			// Video not in queue, add it and play
			const newQueue = [...state.queue, video];
			return {
				...state,
				currentVideo: video,
				isPlaying: true,
				queue: newQueue,
				queueIndex: newQueue.length - 1
			};
		}
	});
}

/**
 * Add video to queue
 */
export function addToQueue(video: VideoOut, position: 'next' | 'end' = 'end') {
	playerState.update((state) => {
		// Don't add duplicates
		if (state.queue.some((v) => v.id === video.id)) {
			return state;
		}

		if (position === 'next') {
			// Insert after current video
			const newQueue = [
				...state.queue.slice(0, state.queueIndex + 1),
				video,
				...state.queue.slice(state.queueIndex + 1)
			];
			return { ...state, queue: newQueue };
		} else {
			// Add to end
			return { ...state, queue: [...state.queue, video] };
		}
	});
}

/**
 * Remove video from queue
 */
export function removeFromQueue(videoId: string) {
	playerState.update((state) => {
		const newQueue = state.queue.filter((v) => v.id !== videoId);
		const newIndex = Math.min(state.queueIndex, newQueue.length - 1);

		return {
			...state,
			queue: newQueue,
			queueIndex: newIndex
		};
	});
}

/**
 * Play next video in queue
 */
export function playNext() {
	playerState.update((state) => {
		if (state.queueIndex < state.queue.length - 1) {
			// Play next in queue
			return {
				...state,
				queueIndex: state.queueIndex + 1,
				currentVideo: state.queue[state.queueIndex + 1],
				isPlaying: true
			};
		} else if (state.repeatMode === 'all' && state.queue.length > 0) {
			// Loop back to start
			return {
				...state,
				queueIndex: 0,
				currentVideo: state.queue[0],
				isPlaying: true
			};
		} else {
			// End of queue
			return {
				...state,
				isPlaying: false
			};
		}
	});
}

/**
 * Play previous video in queue
 */
export function playPrevious() {
	playerState.update((state) => {
		if (state.queueIndex > 0) {
			return {
				...state,
				queueIndex: state.queueIndex - 1,
				currentVideo: state.queue[state.queueIndex - 1],
				isPlaying: true
			};
		}
		return state;
	});
}

/**
 * Jump to specific video in queue
 */
export function jumpToQueueItem(index: number) {
	playerState.update((state) => {
		if (index >= 0 && index < state.queue.length) {
			return {
				...state,
				queueIndex: index,
				currentVideo: state.queue[index],
				isPlaying: true
			};
		}
		return state;
	});
}

/**
 * Clear entire queue and stop playback
 */
export function clearQueue() {
	playerState.update((state) => ({
		...state,
		queue: [],
		queueIndex: 0,
		currentVideo: null,
		isPlaying: false
	}));
}

/**
 * Toggle play/pause
 */
export function togglePlayPause() {
	playerState.update((state) => ({
		...state,
		isPlaying: !state.isPlaying
	}));
}

/**
 * Set volume (0-100)
 */
export function setVolume(volume: number) {
	playerState.update((state) => ({
		...state,
		volume: Math.max(0, Math.min(100, volume))
	}));
}

/**
 * Set player size
 */
export function setPlayerSize(size: PlayerSize) {
	playerState.update((state) => ({
		...state,
		playerSize: size
	}));
}

/**
 * Cycle repeat mode
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
 * Toggle shuffle mode
 */
export function toggleShuffle() {
	playerState.update((state) => ({
		...state,
		shuffleEnabled: !state.shuffleEnabled
	}));
}

/**
 * Close player (stop playback and clear current video)
 */
export function closePlayer() {
	playerState.update((state) => ({
		...state,
		currentVideo: null,
		isPlaying: false
	}));
}
