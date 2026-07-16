<script lang="ts">
	import {
		playerState,
		jumpToQueueItem,
		removeFromQueue,
		clearQueue,
		moveQueueItem
	} from '$lib/stores/playerState.svelte';
	import { formatDuration } from '$lib/utils/formatDuration';
	import { getChannelTitle } from '$lib/utils/channelLookup';
	import type { ChannelOut } from '$lib/types/api';

	interface Props {
		channelMap?: Map<string, ChannelOut>;
	}

	let { channelMap }: Props = $props();

	let dragIndex = $state<number | null>(null);
	let announcement = $state('');
	const isQueueMutable = $derived(playerState.current.queueMutable);

	async function selectQueueItem(index: number) {
		if (playerState.current.isQueueSyncing) return;
		await jumpToQueueItem(index);
	}

	async function remove(videoId: string) {
		if (playerState.current.isQueueSyncing || !isQueueMutable) return;
		await removeFromQueue(videoId);
	}

	async function move(videoId: string, newPosition: number) {
		if (playerState.current.isQueueSyncing || !isQueueMutable) return;
		const video = playerState.current.queue.find((item) => item.id === videoId);
		await moveQueueItem(videoId, newPosition);
		if (!playerState.current.queueError && video) {
			announcement = `Moved ${video.title} to position ${newPosition + 1} of ${playerState.current.queue.length}.`;
		}
	}

	async function drop(index: number) {
		if (dragIndex === null || dragIndex === index) {
			dragIndex = null;
			return;
		}
		const draggedVideo = playerState.current.queue[dragIndex];
		dragIndex = null;
		if (draggedVideo) await move(draggedVideo.id, index);
	}
</script>

<div class="queue-list flex flex-col border-t border-base-300 bg-base-100">
	<div class="flex items-center justify-between border-b border-base-300 px-4 py-2">
		<h2 class="text-sm font-semibold">Queue ({playerState.current.queue.length})</h2>
		<div class="flex items-center gap-2">
			{#if playerState.current.queueMode === 'playlist'}
				<span class="badge badge-sm">Playlist queue</span>
			{/if}
			{#if playerState.current.queue.length > 0 && isQueueMutable}
				<button
					type="button"
					class="btn btn-ghost btn-xs"
					onclick={() => void clearQueue()}
					disabled={playerState.current.isQueueSyncing}
				>
					Clear all
				</button>
			{/if}
		</div>
	</div>

	{#if playerState.current.queueError}
		<p class="px-4 py-2 text-xs text-error" role="alert">{playerState.current.queueError}</p>
	{/if}
	<p class="sr-only" aria-live="polite">{announcement}</p>

	<div class="max-h-96 overflow-y-auto">
		{#if playerState.current.queue.length === 0}
			<div class="flex flex-col items-center justify-center py-8 text-center">
				<svg
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					class="mb-2 h-12 w-12 text-base-content/60"
					aria-hidden="true"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="1.5"
						d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"
					/>
				</svg>
				<p class="text-sm text-base-content/80">Queue is empty</p>
				<p class="text-xs text-base-content/70">Use Play or queue actions on a video</p>
			</div>
		{:else}
			<ol>
				{#each playerState.current.queue as video, index (video.id)}
					{@const isActive = index === playerState.current.queueIndex}
					<li
						class="queue-item flex w-full items-start gap-2 border-b border-base-300 p-2 transition-colors hover:bg-base-200"
						class:active={isActive}
						class:dragging={dragIndex === index}
						draggable={isQueueMutable && !playerState.current.isQueueSyncing}
						ondragstart={() => isQueueMutable && (dragIndex = index)}
						ondragover={(event) => event.preventDefault()}
						ondrop={() => void drop(index)}
					>
						<button
							type="button"
							class="flex min-w-0 flex-1 items-start gap-2 rounded p-1 text-left"
							onclick={() => void selectQueueItem(index)}
							disabled={playerState.current.isQueueSyncing}
							aria-current={isActive ? 'true' : undefined}
							aria-label={`${isActive ? 'Currently playing' : 'Play'} ${video.title}`}
						>
							<span class="flex h-12 w-6 shrink-0 items-center justify-center" aria-hidden="true">
								{#if isActive}
									<svg viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5 text-primary">
										<path
											d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"
										/>
									</svg>
								{:else}
									<span class="text-sm text-base-content/70">{index + 1}</span>
								{/if}
							</span>

							<span class="relative shrink-0">
								{#if video.thumbnail_url}
									<img src={video.thumbnail_url} alt="" class="h-12 w-20 rounded object-cover" />
								{:else}
									<span
										class="flex h-12 w-20 items-center justify-center rounded bg-base-300"
										aria-hidden="true"
									>
										<svg
											viewBox="0 0 24 24"
											fill="none"
											stroke="currentColor"
											class="h-6 w-6 text-base-content/60"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="1.5"
												d="M15.91 11.672a.375.375 0 010 .656l-5.603 3.113a.375.375 0 01-.557-.328V8.887c0-.286.307-.466.557-.327l5.603 3.112z"
											/>
										</svg>
									</span>
								{/if}
								{#if video.duration_seconds}
									<span
										class="absolute right-0.5 bottom-0.5 rounded bg-base-100/90 px-1 text-xs font-semibold"
									>
										{formatDuration(video.duration_seconds)}
									</span>
								{/if}
							</span>

							<span class="min-w-0 flex-1">
								<span class="line-clamp-2 block text-sm font-medium" class:text-primary={isActive}
									>{video.title}</span
								>
								<span class="block truncate text-xs text-base-content/80">
									{channelMap ? getChannelTitle(video.channel_id, channelMap) : video.channel_id}
								</span>
							</span>
						</button>

						{#if isQueueMutable}
							<div class="flex shrink-0 flex-col gap-0.5">
								<button
									type="button"
									class="btn btn-square btn-ghost btn-xs"
									onclick={() => void move(video.id, index - 1)}
									disabled={playerState.current.isQueueSyncing || index === 0}
									aria-label={`Move ${video.title} up`}>↑</button
								>
								<button
									type="button"
									class="btn btn-square btn-ghost btn-xs"
									onclick={() => void move(video.id, index + 1)}
									disabled={playerState.current.isQueueSyncing ||
										index === playerState.current.queue.length - 1}
									aria-label={`Move ${video.title} down`}>↓</button
								>
								<button
									type="button"
									class="btn btn-square btn-ghost btn-xs"
									onclick={() => void remove(video.id)}
									disabled={playerState.current.isQueueSyncing}
									aria-label={`Remove ${video.title} from queue`}>×</button
								>
							</div>
						{/if}
					</li>
				{/each}
			</ol>
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
		background-color: color-mix(in srgb, var(--color-primary) 10%, transparent);
		border-left: 4px solid var(--color-primary);
	}

	.queue-item.dragging {
		opacity: 0.5;
	}
</style>
