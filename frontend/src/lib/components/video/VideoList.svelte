<script lang="ts">
	import type { VideoOut, ChannelOut } from '$lib/types/api';
	import VideoCard from './VideoCard.svelte';
	import EmptyState from '../ui/EmptyState.svelte';
	import { setVideoDisplayMode, uiState } from '$lib/stores/uiState.svelte';

	interface Props {
		videos: VideoOut[];
		channelMap?: Map<string, ChannelOut>;
		onPlay?: (video: VideoOut) => Promise<boolean>;
		showQueueActions?: boolean;
		gridColumns?: number;
	}

	let { videos, channelMap, onPlay, showQueueActions = true, gridColumns = 4 }: Props = $props();
	const displayMode = $derived(uiState.current.videoDisplayMode);
	const safeGridColumns = $derived(Math.max(1, Math.min(6, Math.round(gridColumns))));

	/** Optimistic update for watched-state changes. */
	function handleVideoUpdate(updated: VideoOut) {
		videos = videos.map((v) => (v.id === updated.id ? updated : v));
	}
</script>

<div class="video-list">
	{#if videos.length > 0}
		<div class="mb-3 flex justify-end">
			<div class="join" role="group" aria-label="Video display">
				<button
					type="button"
					class="btn join-item btn-square btn-sm"
					class:btn-active={displayMode === 'list'}
					onclick={() => setVideoDisplayMode('list')}
					aria-label="List view"
					aria-pressed={displayMode === 'list'}
					title="List view"
				>
					<svg
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						class="h-5 w-5"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-width="1.5"
							d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"
						/>
					</svg>
				</button>
				<button
					type="button"
					class="btn join-item btn-square btn-sm"
					class:btn-active={displayMode === 'grid'}
					onclick={() => setVideoDisplayMode('grid')}
					aria-label="Grid view"
					aria-pressed={displayMode === 'grid'}
					title="Grid view"
				>
					<svg
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						class="h-5 w-5"
						aria-hidden="true"
					>
						<path
							stroke-linejoin="round"
							stroke-width="1.5"
							d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"
						/>
					</svg>
				</button>
				<button
					type="button"
					class="btn join-item btn-square btn-sm"
					class:btn-active={displayMode === 'compact'}
					onclick={() => setVideoDisplayMode('compact')}
					aria-label="Compact view"
					aria-pressed={displayMode === 'compact'}
					title="Compact view"
				>
					<svg
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						class="h-5 w-5"
						aria-hidden="true"
					>
						<path stroke-linecap="round" stroke-width="1.5" d="M4 7h16M4 12h16M4 17h16" />
					</svg>
				</button>
			</div>
		</div>

		<div
			class="video-items"
			data-testid="video-items"
			data-display-mode={displayMode}
			style={`--video-grid-columns: ${safeGridColumns}`}
		>
			{#each videos as video (video.id)}
				<VideoCard
					{video}
					{channelMap}
					onUpdate={handleVideoUpdate}
					{onPlay}
					{showQueueActions}
					{displayMode}
				/>
			{/each}
		</div>
	{/if}

	{#if videos.length === 0}
		<EmptyState
			title="No videos found"
			message="Try adjusting your filters or add some channels to get started."
			icon="video"
		/>
	{/if}
</div>

<style>
	.video-items {
		display: grid;
		gap: 0.75rem;
	}

	.video-items[data-display-mode='grid'] {
		grid-template-columns: minmax(0, 1fr);
	}

	.video-items[data-display-mode='compact'] {
		gap: 0.5rem;
	}

	@media (min-width: 40rem) {
		.video-items[data-display-mode='grid'] {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (min-width: 64rem) {
		.video-items[data-display-mode='grid'] {
			grid-template-columns: repeat(3, minmax(0, 1fr));
		}
	}

	@media (min-width: 80rem) {
		.video-items[data-display-mode='grid'] {
			grid-template-columns: repeat(var(--video-grid-columns), minmax(0, 1fr));
		}
	}
</style>
