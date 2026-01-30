<script lang="ts">
	import { onMount } from 'svelte';
	import type { VideoOut, VideoFilters } from '$lib/types/api';
	import { api } from '$lib/api';
	import VideoCard from './VideoCard.svelte';
	import SkeletonCard from '../ui/SkeletonCard.svelte';
	import ErrorState from '../ui/ErrorState.svelte';
	import EmptyState from '../ui/EmptyState.svelte';

	interface Props {
		videos?: VideoOut[];
		initialVideos?: VideoOut[];
		initialTotal?: number;
		initialHasMore?: boolean;
		filters?: VideoFilters;
	}

	let { videos: videosParam, initialVideos = [], initialTotal = 0, initialHasMore = false, filters }: Props = $props();

	// Use either the simple videos prop or the pagination props
	let videos = $state<VideoOut[]>(videosParam ?? initialVideos);
	let total = $state(initialTotal);
	let hasMore = $state(initialHasMore);
	let isLoading = $state(false);
	let error = $state<string | null>(null);
	let offset = $state((videosParam ?? initialVideos).length);

	// Disable infinite scroll if using simple videos prop
	let enableInfiniteScroll = $state(!videosParam);

	let loadMoreTrigger: HTMLDivElement;
	let observer: IntersectionObserver;

	async function loadMore() {
		if (isLoading || !hasMore) return;

		isLoading = true;
		error = null;

		try {
			const response = await api.videos.list({
				...filters,
				limit: 50,
				offset
			});

			videos = [...videos, ...response.items];
			total = response.total;
			hasMore = response.has_more;
			offset += response.items.length;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load more videos';
			console.error('Failed to load more videos:', err);
		} finally {
			isLoading = false;
		}
	}

	function handleVideoUpdate(updated: VideoOut) {
		videos = videos.map((v) => (v.id === updated.id ? updated : v));
	}

	onMount(() => {
		// Only set up intersection observer if infinite scroll is enabled
		if (enableInfiniteScroll) {
			observer = new IntersectionObserver(
				(entries) => {
					if (entries[0].isIntersecting && hasMore && !isLoading) {
						loadMore();
					}
				},
				{
					threshold: 0.1,
					rootMargin: '100px'
				}
			);

			if (loadMoreTrigger) {
				observer.observe(loadMoreTrigger);
			}
		}

		return () => {
			if (observer) {
				observer.disconnect();
			}
		};
	});
</script>

<div class="video-list space-y-4">
	<!-- Video cards -->
	{#each videos as video (video.id)}
		<VideoCard {video} onUpdate={handleVideoUpdate} />
	{/each}

	<!-- Loading skeleton while fetching more -->
	{#if isLoading}
		{#each Array(3) as _}
			<SkeletonCard />
		{/each}
	{/if}

	<!-- Error state -->
	{#if error}
		<ErrorState message={error} onRetry={loadMore} />
	{/if}

	<!-- Load more trigger (invisible) -->
	{#if enableInfiniteScroll && hasMore && !isLoading && !error}
		<div bind:this={loadMoreTrigger} class="h-4"></div>
	{/if}

	<!-- End of list message -->
	{#if enableInfiniteScroll && !hasMore && videos.length > 0 && !isLoading}
		<div class="py-4 text-center text-sm text-base-content/60">
			You've reached the end! ({total} total {total === 1 ? 'video' : 'videos'})
		</div>
	{/if}

	<!-- Empty state -->
	{#if videos.length === 0 && !isLoading && !error}
		<EmptyState
			title="No videos found"
			message="Try adjusting your filters or add some channels to get started."
			icon="video"
		/>
	{/if}
</div>
