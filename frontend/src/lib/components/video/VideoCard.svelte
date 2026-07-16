<script lang="ts">
	import type { VideoOut, ChannelOut } from '$lib/types/api';
	import { formatDuration } from '$lib/utils/formatDuration';
	import { formatRelativeDate } from '$lib/utils/formatDate';
	import { playVideo, addToQueue, playerState } from '$lib/stores/playerState.svelte';
	import { openSaveVideo } from '$lib/stores/modalState.svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { api } from '$lib/api';
	import { getChannelTitle } from '$lib/utils/channelLookup';
	import WatchLaterButton from './WatchLaterButton.svelte';
	import { actionStatus } from '$lib/stores/actionStatus.svelte';
	import { dismissibleDetails } from '$lib/actions/dismissibleDetails';
	import type { VideoDisplayMode } from '$lib/stores/uiState.svelte';

	interface Props {
		video: VideoOut;
		channelMap?: Map<string, ChannelOut>;
		onUpdate?: (video: VideoOut) => void;
		onPlay?: (video: VideoOut) => Promise<boolean>;
		showQueueActions?: boolean;
		displayMode?: VideoDisplayMode;
	}

	let {
		video,
		channelMap,
		onUpdate,
		onPlay,
		showQueueActions = true,
		displayMode = 'list'
	}: Props = $props();

	let isUpdating = $state(false);
	let actionError = $state<string | null>(null);
	let actionMenu = $state<HTMLDetailsElement>();
	const channel = $derived(channelMap?.get(video.channel_id));
	const channelTitle = $derived(
		channelMap ? getChannelTitle(video.channel_id, channelMap) : `Channel ID: ${video.channel_id}`
	);

	async function handleMarkWatched() {
		if (isUpdating) return;

		isUpdating = true;
		actionError = null;
		try {
			const updated = await api.videos.update(video.id, {
				is_watched: !video.is_watched
			});
			onUpdate?.(updated);
			actionStatus.announce(
				updated.is_watched
					? `${video.title} marked as watched.`
					: `${video.title} marked as unwatched.`
			);
		} catch (error) {
			actionError = error instanceof Error ? error.message : 'Watched status could not be updated.';
		} finally {
			isUpdating = false;
		}
	}

	async function handlePlay() {
		actionError = null;
		const started = onPlay ? await onPlay(video) : await playVideo(video);
		if (!started) {
			actionError =
				playerState.current.queueError ?? 'This video could not be opened. Please try again.';
			return;
		}

		const returnUrl = window.location.pathname + window.location.search;
		goto(resolve(`/player?return=${encodeURIComponent(returnUrl)}` as '/player'));
	}

	async function handleAddToQueue(position: 'next' | 'end') {
		closeActionMenu();
		actionError = null;
		await addToQueue(video, position);
		if (playerState.current.queueError) {
			actionError = playerState.current.queueError;
		} else {
			actionStatus.announce(
				position === 'next'
					? `${video.title} will play next.`
					: `${video.title} added to the queue.`
			);
		}
	}

	function closeActionMenu() {
		if (actionMenu) actionMenu.open = false;
	}

	function handleSaveVideo() {
		closeActionMenu();
		openSaveVideo(video);
	}
</script>

<article
	class="rounded-box border border-base-300 bg-base-100 transition-colors hover:border-primary"
	class:opacity-70={video.is_watched}
	aria-labelledby={`video-${video.id}-title`}
	data-display-mode={displayMode}
>
	{#if displayMode === 'compact'}
		<div class="p-2 sm:p-3">
			<div class="flex flex-col gap-2 sm:flex-row sm:items-center">
				<div class="min-w-0 flex-1">
					<button
						type="button"
						class="block max-w-full text-left hover:text-primary"
						onclick={() => void handlePlay()}
						aria-label={`Play ${video.title}`}
					>
						<h3 id={`video-${video.id}-title`} class="truncate leading-tight font-semibold">
							{video.title}
						</h3>
					</button>

					<div class="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-base-content">
						{#if channel}
							<a
								href={resolve('/channels/[id]', { id: channel.id })}
								class="hover:text-primary hover:underline"
							>
								{channelTitle}
							</a>
						{:else}
							<span>{channelTitle}</span>
						{/if}
						<span aria-hidden="true">·</span>
						<span>{formatRelativeDate(video.published_at)}</span>
						{#if video.duration_seconds}<span>{formatDuration(video.duration_seconds)}</span>{/if}
						{#if video.is_short}<span class="badge badge-sm">Short</span>{/if}
						{#if video.is_watched}<span class="badge badge-sm badge-success">Watched</span>{/if}
					</div>
				</div>

				<div class="flex shrink-0 items-center gap-1 self-end sm:self-center">
					<WatchLaterButton videoId={video.id} />
					<button
						type="button"
						class="btn btn-square btn-ghost btn-sm"
						class:btn-active={video.is_watched}
						onclick={() => void handleMarkWatched()}
						disabled={isUpdating}
						aria-label={video.is_watched ? 'Mark as unwatched' : 'Mark as watched'}
						aria-pressed={video.is_watched}
					>
						{#if isUpdating}
							<span class="loading loading-xs loading-spinner" aria-hidden="true"></span>
						{:else}
							<svg
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								class="h-5 w-5"
								aria-hidden="true"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
								/>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
								/>
							</svg>
						{/if}
					</button>

					{#if showQueueActions}
						<details bind:this={actionMenu} class="dropdown dropdown-end" use:dismissibleDetails>
							<summary class="btn btn-ghost btn-sm" aria-label={`More actions for ${video.title}`}
								>More</summary
							>
							<ul
								class="dropdown-content menu z-10 mt-1 w-44 rounded-box border border-base-300 bg-base-100 p-1 shadow-sm"
							>
								<li><button type="button" onclick={handleSaveVideo}>Save to playlist</button></li>
								<li>
									<button type="button" onclick={() => void handleAddToQueue('next')}
										>Play next</button
									>
								</li>
								<li>
									<button type="button" onclick={() => void handleAddToQueue('end')}
										>Add to queue</button
									>
								</li>
							</ul>
						</details>
					{/if}
				</div>
			</div>

			{#if actionError}
				<p class="mt-2 text-sm text-error" role="alert">
					{actionError}
					<button type="button" class="btn ml-1 btn-link btn-xs" onclick={() => void handlePlay()}>
						Retry
					</button>
				</p>
			{/if}
		</div>
	{:else}
		<div class="video-card-body p-3 sm:p-4">
			<div class="video-card-layout grid gap-3 sm:grid-cols-[10rem_minmax(0,1fr)] sm:gap-4">
				<div class="relative min-w-0">
					<button
						type="button"
						class="group relative block aspect-video w-full overflow-hidden rounded-lg bg-base-300 text-base-content focus-visible:outline-offset-2"
						onclick={() => void handlePlay()}
						aria-label={`Play ${video.title}`}
					>
						{#if video.thumbnail_url}
							<img
								src={video.thumbnail_url}
								alt=""
								class="h-full w-full object-cover transition-opacity group-hover:opacity-90"
							/>
						{:else}
							<span class="flex h-full w-full items-center justify-center" aria-hidden="true">
								<svg
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									class="h-9 w-9 text-base-content/60"
								>
									<path
										stroke-linecap="round"
										stroke-width="1.5"
										d="M15.91 11.672a.375.375 0 010 .656l-5.603 3.113a.375.375 0 01-.557-.328V8.887c0-.286.307-.466.557-.327l5.603 3.112z"
									/>
								</svg>
							</span>
						{/if}
						<span
							class="absolute inset-0 flex items-center justify-center opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100"
							aria-hidden="true"
						>
							<span class="rounded-full bg-base-100/90 p-2 shadow-sm">
								<svg viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5">
									<path
										d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"
									/>
								</svg>
							</span>
						</span>
					</button>

					<div class="absolute top-1 right-1 z-10 rounded-full bg-base-100/90">
						<WatchLaterButton videoId={video.id} />
					</div>

					{#if video.duration_seconds}
						<span
							class="pointer-events-none absolute right-1 bottom-1 rounded bg-base-100/90 px-1.5 py-0.5 text-xs font-semibold"
						>
							{formatDuration(video.duration_seconds)}
						</span>
					{/if}

					{#if video.is_watched}
						<span
							class="pointer-events-none absolute top-1 left-1 rounded-full bg-success p-1 text-success-content"
							aria-label="Watched"
						>
							<svg viewBox="0 0 20 20" fill="currentColor" class="h-3 w-3" aria-hidden="true">
								<path
									fill-rule="evenodd"
									d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
									clip-rule="evenodd"
								/>
							</svg>
						</span>
					{/if}
				</div>

				<div class="flex min-w-0 flex-col">
					<button
						type="button"
						class="w-fit max-w-full text-left hover:text-primary"
						onclick={() => void handlePlay()}
						aria-label={`Play ${video.title}`}
					>
						<h3 id={`video-${video.id}-title`} class="line-clamp-2 leading-tight font-semibold">
							{video.title}
						</h3>
					</button>

					{#if channel}
						<a
							href={resolve('/channels/[id]', { id: channel.id })}
							class="mt-1 w-fit text-sm text-base-content hover:text-primary hover:underline"
						>
							{channelTitle}
						</a>
					{:else}
						<p class="mt-1 text-sm text-base-content">{channelTitle}</p>
					{/if}

					<p class="mt-0.5 text-xs text-base-content">
						{formatRelativeDate(video.published_at)}
						{#if video.is_short}<span class="ml-2 badge badge-sm">Short</span>{/if}
					</p>

					<div class="mt-auto flex flex-wrap items-center gap-1 pt-2">
						<button
							type="button"
							class="btn btn-square btn-ghost btn-sm"
							class:btn-active={video.is_watched}
							onclick={() => void handleMarkWatched()}
							disabled={isUpdating}
							aria-label={video.is_watched ? 'Mark as unwatched' : 'Mark as watched'}
							aria-pressed={video.is_watched}
						>
							{#if isUpdating}
								<span class="loading loading-xs loading-spinner" aria-hidden="true"></span>
							{:else}
								<svg
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									class="h-5 w-5"
									aria-hidden="true"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="1.5"
										d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
									/>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="1.5"
										d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
									/>
								</svg>
							{/if}
						</button>

						{#if showQueueActions}
							<details
								bind:this={actionMenu}
								class="dropdown dropdown-end ml-auto"
								use:dismissibleDetails
							>
								<summary
									class="btn btn-ghost btn-sm"
									aria-label={`More actions for ${video.title}`}
								>
									More
								</summary>
								<ul
									class="dropdown-content menu z-10 mt-1 w-44 rounded-box border border-base-300 bg-base-100 p-1 shadow-sm"
								>
									<li>
										<button type="button" onclick={handleSaveVideo}>Save to playlist</button>
									</li>
									<li>
										<button type="button" onclick={() => void handleAddToQueue('next')}
											>Play next</button
										>
									</li>
									<li>
										<button type="button" onclick={() => void handleAddToQueue('end')}
											>Add to queue</button
										>
									</li>
								</ul>
							</details>
						{/if}
					</div>

					{#if actionError}
						<p class="mt-2 text-sm text-error" role="alert">
							{actionError}
							<button
								type="button"
								class="btn ml-1 btn-link btn-xs"
								onclick={() => void handlePlay()}
							>
								Retry
							</button>
						</p>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</article>

<style>
	article[data-display-mode='grid'] {
		height: 100%;
	}

	article[data-display-mode='grid'] .video-card-body,
	article[data-display-mode='grid'] .video-card-layout {
		height: 100%;
	}

	article[data-display-mode='grid'] .video-card-layout {
		grid-template-columns: minmax(0, 1fr);
	}

	.line-clamp-2 {
		display: -webkit-box;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
