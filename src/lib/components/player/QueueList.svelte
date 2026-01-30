<script lang="ts">
	import { playerState, jumpToQueueItem, removeFromQueue, clearQueue } from '$lib/stores/playerState.svelte';
	import { formatDuration } from '$lib/utils/formatDuration';

	let isDragging = $state(false);
</script>

<div class="queue-list flex flex-col border-t border-base-300 bg-base-100">
	<!-- Header -->
	<div class="flex items-center justify-between border-b border-base-300 px-4 py-2">
		<h3 class="text-sm font-semibold">
			Queue ({playerState.current.queue.length})
		</h3>
		{#if playerState.current.queue.length > 0}
			<button class="btn btn-ghost btn-xs" onclick={clearQueue}>Clear All</button>
		{/if}
	</div>

	<!-- Queue items -->
	<div class="max-h-96 overflow-y-auto">
		{#if playerState.current.queue.length === 0}
			<div class="flex flex-col items-center justify-center py-8 text-center">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="mb-2 h-12 w-12 text-base-content/40"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"
					/>
				</svg>
				<p class="text-sm text-base-content/60">Queue is empty</p>
				<p class="text-xs text-base-content/40">Click play on videos to add them</p>
			</div>
		{:else}
			{#each playerState.current.queue as video, index (video.id)}
				{@const isActive = index === playerState.current.queueIndex}
				<div
					class="queue-item flex w-full cursor-pointer items-start gap-3 border-b border-base-300 p-3 text-left transition-colors hover:bg-base-200"
					class:active={isActive}
					role="button"
					tabindex="0"
					onclick={() => jumpToQueueItem(index)}
					onkeydown={(e) => e.key === 'Enter' && jumpToQueueItem(index)}
				>
					<!-- Index / Playing indicator -->
					<div class="flex h-12 w-8 shrink-0 items-center justify-center">
						{#if index === playerState.current.queueIndex}
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
								class="h-5 w-5 text-primary"
							>
								<path
									d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"
								/>
							</svg>
						{:else}
							<span class="text-sm text-base-content/60">{index + 1}</span>
						{/if}
					</div>

					<!-- Thumbnail -->
					<div class="relative shrink-0">
						{#if video.thumbnail_url}
							<img
								src={video.thumbnail_url}
								alt={video.title}
								class="h-12 w-20 rounded object-cover"
							/>
						{:else}
							<div class="flex h-12 w-20 items-center justify-center rounded bg-base-300">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="h-6 w-6 text-base-content/40"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
									/>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M15.91 11.672a.375.375 0 010 .656l-5.603 3.113a.375.375 0 01-.557-.328V8.887c0-.286.307-.466.557-.327l5.603 3.112z"
									/>
								</svg>
							</div>
						{/if}

						<!-- Duration -->
						{#if video.duration_seconds}
							<div
								class="absolute bottom-0.5 right-0.5 rounded bg-base-100/90 px-1 text-xs font-semibold"
							>
								{formatDuration(video.duration_seconds)}
							</div>
						{/if}
					</div>

					<!-- Video info -->
					<div class="min-w-0 flex-1">
						<p class="line-clamp-2 text-sm font-medium" class:text-primary={isActive}>
							{video.title}
						</p>
						<p class="text-xs text-base-content/60">
							{video.channel_id}
						</p>
					</div>

					<!-- Remove button -->
					<button
						class="btn btn-ghost btn-sm btn-square shrink-0"
						onclick={(e) => {
							e.stopPropagation();
							removeFromQueue(video.id);
						}}
						aria-label="Remove from queue"
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
			{/each}
		{/if}
	</div>
</div>

<style>
	.line-clamp-2 {
		display: -webkit-box;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.queue-item.active {
		background-color: oklch(var(--p) / 0.1);
		border-left: 4px solid oklch(var(--p));
	}
</style>
