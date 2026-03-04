// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		interface Locals {
			authToken: string | null;
		}
	}

	// YouTube IFrame API types
	interface Window {
		onYouTubeIframeAPIReady?: () => void;
		YT: typeof YT;
	}

	namespace YT {
		interface Player {
			loadVideoById(videoId: string): void;
			playVideo(): void;
			pauseVideo(): void;
			stopVideo(): void;
			setVolume(volume: number): void;
			getVolume(): number;
			mute(): void;
			unMute(): void;
			destroy(): void;
		}

		interface PlayerEvent {
			target: Player;
		}

		interface OnStateChangeEvent {
			target: Player;
			data: number;
		}

		interface OnErrorEvent {
			target: Player;
			data: number;
		}

		enum PlayerState {
			UNSTARTED = -1,
			ENDED = 0,
			PLAYING = 1,
			PAUSED = 2,
			BUFFERING = 3,
			CUED = 5
		}

		interface PlayerOptions {
			height?: string | number;
			width?: string | number;
			videoId?: string;
			playerVars?: PlayerVars;
			events?: Events;
		}

		interface PlayerVars {
			autoplay?: 0 | 1;
			controls?: 0 | 1;
			modestbranding?: 0 | 1;
			rel?: 0 | 1;
			fs?: 0 | 1;
			playsinline?: 0 | 1;
		}

		interface Events {
			onReady?: (event: PlayerEvent) => void;
			onStateChange?: (event: OnStateChangeEvent) => void;
			onError?: (event: OnErrorEvent) => void;
		}

		class Player {
			constructor(elementId: string | HTMLElement, options: PlayerOptions);
		}
	}
}

export {};
