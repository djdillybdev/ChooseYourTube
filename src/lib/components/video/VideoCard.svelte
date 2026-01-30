<script lang="ts">
	import type { VideoOut } from '$lib/types/api';
	import { formatDuration } from '$lib/utils/formatDuration';
	import { formatRelativeDate } from '$lib/utils/formatDate';
	import { playVideo, playerState } from '$lib/stores/playerState.svelte';
	import { api } from '$lib/api';

	interface Props {
		video: VideoOut;
		onUpdate?: (video: VideoOut) => void;
	}

	let { video, onUpdate }: Props = $props();

	let isHovered = $state(false);
	let isUpdating = $state(false);

	async function handleMarkWatched(e: MouseEvent) {
		e.stopPropagation();
		if (isUpdating) return;

		isUpdating = true;
		try {
			const updated = await api.videos.update(video.id, {
				is_watched: !video.is_watched
			});
			onUpdate?.(updated);
		} catch (error) {
			console.error('Failed to update watched status:', error);
		} finally {
			isUpdating = false;
		}
	}

	async function handleToggleFavorite(e: MouseEvent) {
		e.stopPropagation();
		if (isUpdating) return;

		isUpdating = true;
		try {
			const updated = await api.videos.update(video.id, {
				is_favorited: !video.is_favorited
			});
			onUpdate?.(updated);
		} catch (error) {
			console.error('Failed to update favorite status:', error);
		} finally {
			isUpdating = false;
		}
	}

	function handlePlay() {
		console.log('🎬 VideoCard: handlePlay called for video:', video.title, video.id);
		playVideo(video);
		console.log('🎬 VideoCard: playVideo() completed, playerState:', playerState.current);
	}
</script>

<div
	class="video-card card bg-base-100 shadow-sm transition-all duration-200 hover:shadow-md"
	class:opacity-60={video.is_watched}
	onmouseenter={() => (isHovered = true)}
	onmouseleave={() => (isHovered = false)}
	onclick={handlePlay}
	role="button"
	tabindex="0"
	onkeydown={(e) => e.key === 'Enter' && handlePlay()}
>
	<div class="card-body p-4">
		<div class="flex gap-4">
			<!-- Thumbnail -->
			<div class="relative shrink-0">
				{#if video.thumbnail_url}
					<img
						src={video.thumbnail_url}
						alt={video.title}
						class="h-24 w-40 rounded-lg object-cover"
					/>
				{:else}
					<div class="flex h-24 w-40 items-center justify-center rounded-lg bg-base-300">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="h-8 w-8 text-base-content/40"
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

				<!-- Duration overlay -->
				{#if video.duration_seconds}
					<div
						class="absolute bottom-1 right-1 rounded bg-base-100/90 px-1.5 py-0.5 text-xs font-semibold"
					>
						{formatDuration(video.duration_seconds)}
					</div>
				{/if}

				<!-- Watched indicator -->
				{#if video.is_watched}
					<div class="absolute left-1 top-1 rounded-full bg-success p-1">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="h-3 w-3 text-success-content"
						>
							<path
								fill-rule="evenodd"
								d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
				{/if}
			</div>

			<!-- Content -->
			<div class="flex min-w-0 flex-1 flex-col justify-between">
				<!-- Title and metadata -->
				<div>
					<h3 class="line-clamp-2 font-semibold leading-tight">{video.title}</h3>
					<p class="mt-1 text-sm text-base-content/60">Channel ID: {video.channel_id}</p>
					<p class="text-xs text-base-content/40">
						{formatRelativeDate(video.published_at)}
						{#if video.is_short}
							<span class="badge badge-sm ml-2">Short</span>
						{/if}
					</p>
				</div>

				<!-- Actions (shown on hover) -->
				{#if isHovered}
					<div class="mt-2 flex gap-2">
						<button
							class="btn btn-ghost btn-sm btn-square"
							class:btn-active={video.is_watched}
							onclick={handleMarkWatched}
							disabled={isUpdating}
							aria-label={video.is_watched ? 'Mark as unwatched' : 'Mark as watched'}
							title={video.is_watched ? 'Mark as unwatched' : 'Mark as watched'}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill={video.is_watched ? 'currentColor' : 'none'}
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="h-5 w-5"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
								/>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
								/>
							</svg>
						</button>

						<button
							class="btn btn-ghost btn-sm btn-square"
							class:btn-active={video.is_favorited}
							class:text-warning={video.is_favorited}
							onclick={handleToggleFavorite}
							disabled={isUpdating}
							aria-label={video.is_favorited ? 'Remove from favorites' : 'Add to favorites'}
							title={video.is_favorited ? 'Remove from favorites' : 'Add to favorites'}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill={video.is_favorited ? 'currentColor' : 'none'}
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="h-5 w-5"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
								/>
							</svg>
						</button>

						<button
							class="btn btn-primary btn-sm gap-1"
							onclick={(e) => {
								e.stopPropagation();
								handlePlay();
							}}
							aria-label="Play video"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
								class="h-4 w-4"
							>
								<path
									d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"
								/>
							</svg>
							Play
						</button>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.video-card {
		cursor: pointer;
	}

	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
