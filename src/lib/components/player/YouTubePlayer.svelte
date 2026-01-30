<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { playerState, playNext, togglePlayPause } from '$lib/stores/playerState.svelte';

	let playerElement: HTMLDivElement;
	let player: YT.Player | null = null;
	let isReady = $state(false);

	function initializePlayer() {
		if (!playerElement || !window.YT || player) return;

		player = new window.YT.Player(playerElement, {
			height: '100%',
			width: '100%',
			videoId: playerState.current.currentVideo?.id || '',
			playerVars: {
				autoplay: 1,
				controls: 0, // We'll use custom controls
				modestbranding: 1,
				rel: 0,
				fs: 1 // Allow fullscreen
			},
			events: {
				onReady: handlePlayerReady,
				onStateChange: handleStateChange,
				onError: handleError
			}
		});
	}

	function handlePlayerReady(event: YT.PlayerEvent) {
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
		} else if (
			state === window.YT.PlayerState.PAUSED ||
			state === window.YT.PlayerState.BUFFERING
		) {
			playerState.update((s) => ({ ...s, isPlaying: false }));
		} else if (state === window.YT.PlayerState.ENDED) {
			// Video ended, play next
			playNext();
		}
	}

	function handleError(event: YT.OnErrorEvent) {
		console.error('YouTube Player Error:', event.data);
		// Skip to next video on error
		playNext();
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
		<div
			class="absolute inset-0 flex items-center justify-center bg-black/80 text-base-content"
		>
			<span class="loading loading-spinner loading-lg"></span>
		</div>
	{/if}
</div>
