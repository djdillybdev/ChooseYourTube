<script lang="ts">
	import {
		playerState,
		togglePlayPause,
		playNext,
		playPrevious,
		setVolume,
		cycleRepeatMode
	} from '$lib/stores/playerState.svelte';
	import { formatDuration } from '$lib/utils/formatDuration';

	interface Props {
		onToggleQueue?: () => void;
		showQueue?: boolean;
	}

	let { onToggleQueue, showQueue = false }: Props = $props();

	let isMuted = $state(false);

	function handleVolumeChange(e: Event) {
		const target = e.target as HTMLInputElement;
		setVolume(Number(target.value));
		if (Number(target.value) > 0) {
			isMuted = false;
		}
	}

	function toggleMute() {
		if (isMuted) {
			setVolume(75);
			isMuted = false;
		} else {
			setVolume(0);
			isMuted = true;
		}
	}

	function getRepeatIcon() {
		switch (playerState.current.repeatMode) {
			case 'one':
				return 'repeat-one';
			case 'all':
				return 'repeat';
			default:
				return 'repeat-off';
		}
	}
</script>

<div class="player-controls flex items-center gap-2 border-t border-base-300 bg-base-100 p-3">
	<!-- Play/Pause and Skip -->
	<div class="flex items-center gap-1">
		<button
			class="btn btn-square btn-ghost btn-sm"
			onclick={playPrevious}
			disabled={playerState.current.queueIndex === 0}
			aria-label="Previous"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 20 20"
				fill="currentColor"
				class="h-5 w-5"
			>
				<path
					d="M7.712 4.819A1.5 1.5 0 0110 6.095v2.973c.104-.131.234-.248.389-.344l6.323-3.905A1.5 1.5 0 0119 6.095v7.81a1.5 1.5 0 01-2.288 1.276l-6.323-3.905a1.505 1.505 0 01-.389-.344v2.973a1.5 1.5 0 01-2.288 1.276l-6.323-3.905a1.5 1.5 0 010-2.552l6.323-3.905z"
				/>
			</svg>
		</button>

		<button
			class="btn btn-circle btn-sm btn-primary"
			onclick={togglePlayPause}
			aria-label={playerState.current.isPlaying ? 'Pause' : 'Play'}
		>
			{#if playerState.current.isPlaying}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="h-5 w-5"
				>
					<path
						d="M5.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75A.75.75 0 007.25 3h-1.5zM12.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75a.75.75 0 00-.75-.75h-1.5z"
					/>
				</svg>
			{:else}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="h-5 w-5"
				>
					<path
						d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"
					/>
				</svg>
			{/if}
		</button>

		<button
			class="btn btn-square btn-ghost btn-sm"
			onclick={playNext}
			disabled={!playerState.current.queue.length ||
				(playerState.current.queueIndex >= playerState.current.queue.length - 1 &&
					playerState.current.repeatMode !== 'all')}
			aria-label="Next"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 20 20"
				fill="currentColor"
				class="h-5 w-5"
			>
				<path
					d="M12.288 4.819A1.5 1.5 0 0010 6.095v2.973c-.104-.131-.234-.248-.389-.344L3.288 4.819A1.5 1.5 0 001 6.095v7.81a1.5 1.5 0 002.288 1.276l6.323-3.905c.155-.096.285-.213.389-.344v2.973a1.5 1.5 0 002.288 1.276l6.323-3.905a1.5 1.5 0 000-2.552l-6.323-3.905z"
				/>
			</svg>
		</button>
	</div>

	<!-- Video title (truncated) -->
	<div class="min-w-0 flex-1">
		{#if playerState.current.currentVideo}
			<div class="truncate text-sm font-medium">
				{playerState.current.currentVideo.title}
			</div>
			<div class="text-xs text-base-content/60">
				{playerState.current.queueIndex + 1} / {playerState.current.queue.length || 1}
			</div>
		{/if}
	</div>

	<!-- Volume control -->
	<div class="flex items-center gap-2">
		<button
			class="btn btn-square btn-ghost btn-sm"
			onclick={toggleMute}
			aria-label={isMuted ? 'Unmute' : 'Mute'}
		>
			{#if isMuted || playerState.current.volume === 0}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="h-5 w-5"
				>
					<path
						d="M10.047 3.062a.75.75 0 01.453.688v12.5a.75.75 0 01-1.264.546L5.203 13H2.667a.75.75 0 01-.7-.48A6.985 6.985 0 011.5 10c0-.887.165-1.737.468-2.52a.75.75 0 01.7-.48h2.535l4.033-3.796a.75.75 0 01.811-.142zM13.78 7.22a.75.75 0 10-1.06 1.06L14.44 10l-1.72 1.72a.75.75 0 001.06 1.06l1.72-1.72 1.72 1.72a.75.75 0 101.06-1.06L16.56 10l1.72-1.72a.75.75 0 00-1.06-1.06L15.5 8.94l-1.72-1.72z"
					/>
				</svg>
			{:else if playerState.current.volume < 50}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="h-5 w-5"
				>
					<path
						d="M10.047 3.062a.75.75 0 01.453.688v12.5a.75.75 0 01-1.264.546L5.203 13H2.667a.75.75 0 01-.7-.48A6.985 6.985 0 011.5 10c0-.887.165-1.737.468-2.52a.75.75 0 01.7-.48h2.535l4.033-3.796a.75.75 0 01.811-.142zM13.5 10a2.252 2.252 0 00-1.318-2.049.75.75 0 11.636-1.36A3.752 3.752 0 0115 10a3.752 3.752 0 01-2.182 3.41.75.75 0 11-.636-1.362A2.252 2.252 0 0013.5 10z"
					/>
				</svg>
			{:else}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="h-5 w-5"
				>
					<path
						d="M10.5 3.75a.75.75 0 00-1.264-.546L5.203 7H2.667a.75.75 0 00-.7.48A6.985 6.985 0 001.5 10c0 .887.165 1.737.468 2.52.111.29.39.48.7.48h2.535l4.033 3.796a.75.75 0 001.264-.546V3.75zM16.45 5.05a.75.75 0 00-1.06 1.061 5.5 5.5 0 010 7.778.75.75 0 001.06 1.06 7 7 0 000-9.899z"
					/>
					<path
						d="M14.329 7.172a.75.75 0 00-1.061 1.06 2.5 2.5 0 010 3.536.75.75 0 001.06 1.06 4 4 0 000-5.656z"
					/>
				</svg>
			{/if}
		</button>

		<input
			type="range"
			min="0"
			max="100"
			value={playerState.current.volume}
			oninput={handleVolumeChange}
			class="range w-20 range-primary range-xs"
			aria-label="Volume"
		/>
	</div>

	<!-- Repeat mode -->
	<button
		class="btn btn-square btn-ghost btn-sm"
		class:btn-active={playerState.current.repeatMode !== 'none'}
		onclick={cycleRepeatMode}
		aria-label="Repeat: {playerState.current.repeatMode}"
		title="Repeat: {playerState.current.repeatMode}"
	>
		{#if playerState.current.repeatMode === 'one'}
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class="h-5 w-5"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M19.5 12c0-1.232-.046-2.453-.138-3.662a4.006 4.006 0 00-3.7-3.7 48.678 48.678 0 00-7.324 0 4.006 4.006 0 00-3.7 3.7c-.017.22-.032.441-.046.662M19.5 12l3-3m-3 3l-3-3m-12 3c0 1.232.046 2.453.138 3.662a4.006 4.006 0 003.7 3.7 48.656 48.656 0 007.324 0 4.006 4.006 0 003.7-3.7c.017-.22.032-.441.046-.662M4.5 12l3 3m-3-3l-3 3"
				/>
			</svg>
			<span class="absolute right-1 bottom-1 text-xs font-bold">1</span>
		{:else}
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill={playerState.current.repeatMode === 'all' ? 'currentColor' : 'none'}
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class="h-5 w-5"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M19.5 12c0-1.232-.046-2.453-.138-3.662a4.006 4.006 0 00-3.7-3.7 48.678 48.678 0 00-7.324 0 4.006 4.006 0 00-3.7 3.7c-.017.22-.032.441-.046.662M19.5 12l3-3m-3 3l-3-3m-12 3c0 1.232.046 2.453.138 3.662a4.006 4.006 0 003.7 3.7 48.656 48.656 0 007.324 0 4.006 4.006 0 003.7-3.7c.017-.22.032-.441.046-.662M4.5 12l3 3m-3-3l-3 3"
				/>
			</svg>
		{/if}
	</button>

	<!-- Queue toggle -->
	{#if onToggleQueue}
		<button
			class="btn btn-square btn-ghost btn-sm"
			class:btn-active={showQueue}
			onclick={onToggleQueue}
			aria-label="Toggle queue"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class="h-5 w-5"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"
				/>
			</svg>
			{#if playerState.current.queue.length > 0}
				<div class="absolute -top-1 -right-1 badge badge-xs badge-primary">
					{playerState.current.queue.length}
				</div>
			{/if}
		</button>
	{/if}
</div>
