<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import { api } from '$lib/api';
	import { playerState, playNext } from '$lib/stores/playerState.svelte';

	interface Props {
		onPlaybackError?: (title: string) => void;
	}

	let { onPlaybackError = () => undefined }: Props = $props();

	let playerElement: HTMLDivElement;
	let player: YT.Player | null = null;
	let isReady = $state(false);
	let isAdvancingQueue = false;
	const watchedUpdatesInFlight = new SvelteSet<string>();

	async function markCurrentVideoWatched() {
		const video = playerState.current.currentVideo;
		if (!video || video.is_watched || watchedUpdatesInFlight.has(video.id)) return;

		watchedUpdatesInFlight.add(video.id);
		try {
			const updatedVideo = await api.videos.update(video.id, { is_watched: true });
			playerState.update((state) => ({
				...state,
				currentVideo:
					state.currentVideo?.id === updatedVideo.id ? updatedVideo : state.currentVideo,
				queue: state.queue.map((item) => (item.id === updatedVideo.id ? updatedVideo : item))
			}));
		} catch (error) {
			console.error('Failed to mark video as watched:', error);
		} finally {
			watchedUpdatesInFlight.delete(video.id);
		}
	}

	function initializePlayer() {
		if (!playerElement || !window.YT || player) return;

		player = new window.YT.Player(playerElement, {
			height: '100%',
			width: '100%',
			videoId: playerState.current.currentVideo?.id || '',
			playerVars: {
				autoplay: 1,
				controls: 1,
				modestbranding: 1,
				rel: 0,
				fs: 1, // Allow fullscreen
				playsinline: 1
			},
			events: {
				onReady: handlePlayerReady,
				onStateChange: handleStateChange,
				onError: handleError
			}
		});
	}

	function handlePlayerReady() {
		isReady = true;
		if (playerState.current.currentVideo) {
			player?.loadVideoById(playerState.current.currentVideo.id);
			if (playerState.current.isPlaying) {
				player?.playVideo();
			}
		}
		// Set initial volume
		player?.setVolume(playerState.current.volume);
	}

	function handleStateChange(event: YT.OnStateChangeEvent) {
		const state = event.data;

		// Update playing state
		if (state === window.YT.PlayerState.PLAYING) {
			playerState.update((s) => ({ ...s, isPlaying: true }));
			void markCurrentVideoWatched();
		} else if (state === window.YT.PlayerState.PAUSED) {
			playerState.update((s) => ({ ...s, isPlaying: false }));
		} else if (state === window.YT.PlayerState.ENDED) {
			// Video ended, play next
			if (!isAdvancingQueue) {
				isAdvancingQueue = true;
				void playNext().finally(() => {
					isAdvancingQueue = false;
				});
			}
		}
	}

	function handleError(event: YT.OnErrorEvent) {
		console.error('YouTube Player Error:', event.data);
		onPlaybackError(playerState.current.currentVideo?.title ?? 'This video');
		// Skip to next video on error
		if (!isAdvancingQueue) {
			isAdvancingQueue = true;
			void playNext().finally(() => {
				isAdvancingQueue = false;
			});
		}
	}

	// Watch for video changes
	$effect(() => {
		if (player && isReady && playerState.current.currentVideo) {
			player.loadVideoById(playerState.current.currentVideo.id);
		}
	});

	// Watch for play/pause changes
	$effect(() => {
		if (player && isReady) {
			if (playerState.current.isPlaying) {
				player.playVideo();
			} else {
				player.pauseVideo();
			}
		}
	});

	// Watch for volume changes
	$effect(() => {
		if (player && isReady) {
			player.setVolume(playerState.current.volume);
		}
	});

	onMount(() => {
		// Wait for YouTube API to be ready
		if (window.YT && window.YT.Player) {
			initializePlayer();
		} else {
			// YouTube API not loaded yet, wait for it
			window.onYouTubeIframeAPIReady = () => {
				initializePlayer();
			};
		}
	});

	onDestroy(() => {
		if (player) {
			player.destroy();
			player = null;
		}
	});
</script>

<div class="youtube-player relative aspect-video w-full overflow-hidden rounded-lg bg-black">
	<div bind:this={playerElement} class="h-full w-full"></div>

	{#if !isReady}
		<div class="absolute inset-0 flex items-center justify-center bg-black/80 text-base-content">
			<span class="loading loading-lg loading-spinner"></span>
		</div>
	{/if}
</div>
