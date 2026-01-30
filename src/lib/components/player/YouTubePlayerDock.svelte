<script lang="ts">
	import { playerState, closePlayer, setPlayerSize, type PlayerSize } from '$lib/stores/playerState.svelte';
	import YouTubePlayer from './YouTubePlayer.svelte';
	import PlayerControls from './PlayerControls.svelte';
	import QueueList from './QueueList.svelte';

	let showQueue = $state(false);
	let isMinimized = $state(false);

	function toggleQueue() {
		showQueue = !showQueue;
	}

	function toggleMinimize() {
		isMinimized = !isMinimized;
	}

	function handleClose() {
		closePlayer();
		showQueue = false;
		isMinimized = false;
	}

	// Determine player width based on size
	const playerWidths: Record<PlayerSize, string> = {
		mini: '320px',
		compact: '480px',
		expanded: '640px'
	};
</script>

<div
	class="player-dock fixed bottom-4 right-4 z-50 flex flex-col overflow-hidden rounded-lg border border-base-300 bg-base-100 shadow-2xl transition-all duration-300"
	style="width: {playerWidths[playerState.current.playerSize]};"
	class:minimized={isMinimized}
>
	<!-- Header bar -->
	<div class="flex items-center justify-between border-b border-base-300 bg-base-200 px-3 py-2">
		<div class="flex items-center gap-2">
			<button
				class="btn btn-ghost btn-xs btn-square"
				onclick={toggleMinimize}
				aria-label={isMinimized ? 'Restore' : 'Minimize'}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="h-4 w-4"
				>
					{#if isMinimized}
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15"
						/>
					{:else}
						<path stroke-linecap="round" stroke-linejoin="round" d="M19.5 12h-15" />
					{/if}
				</svg>
			</button>

			<span class="text-xs font-semibold">Now Playing</span>
		</div>

		<div class="flex items-center gap-1">
			<!-- Size controls -->
			<div class="join join-horizontal">
				<button
					class="btn btn-xs join-item"
					class:btn-active={playerState.current.playerSize === 'mini'}
					onclick={() => setPlayerSize('mini')}
					title="Mini"
				>
					S
				</button>
				<button
					class="btn btn-xs join-item"
					class:btn-active={playerState.current.playerSize === 'compact'}
					onclick={() => setPlayerSize('compact')}
					title="Compact"
				>
					M
				</button>
				<button
					class="btn btn-xs join-item"
					class:btn-active={playerState.current.playerSize === 'expanded'}
					onclick={() => setPlayerSize('expanded')}
					title="Expanded"
				>
					L
				</button>
			</div>

			<!-- Close button -->
			<button
				class="btn btn-ghost btn-xs btn-square"
				onclick={handleClose}
				aria-label="Close player"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="h-4 w-4"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>
	</div>

	{#if !isMinimized}
		<!-- Player -->
		<div class="player-container">
			<YouTubePlayer />
		</div>

		<!-- Controls -->
		<PlayerControls onToggleQueue={toggleQueue} {showQueue} />

		<!-- Queue (collapsible) -->
		{#if showQueue}
			<QueueList />
		{/if}
	{/if}
</div>

<style>
	.player-dock.minimized {
		width: 280px !important;
	}
</style>
