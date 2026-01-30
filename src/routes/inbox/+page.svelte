<script lang="ts">
	import type { VideoOut } from '$lib/types/api';
	import VideoList from '$lib/components/video/VideoList.svelte';
	import ErrorState from '$lib/components/ui/ErrorState.svelte';
	import { filterState } from '$lib/stores/filterState.svelte';

	interface Props {
		data: {
			videos: VideoOut[];
			total: number;
			hasMore: boolean;
			error?: string;
		};
	}

	let { data }: Props = $props();
</script>

<div class="container mx-auto max-w-4xl p-6">
	<!-- Page Header -->
	<div class="mb-6">
		<h1 class="text-3xl font-bold">Inbox</h1>
		<p class="text-sm text-base-content/60">
			{data.total} unwatched {data.total === 1 ? 'video' : 'videos'}
		</p>
	</div>

	<!-- Error State (from initial load) -->
	{#if data.error}
		<ErrorState message={data.error} />
	{:else}
		<!-- Video List with infinite scroll -->
		<VideoList
			initialVideos={data.videos}
			initialTotal={data.total}
			initialHasMore={data.hasMore}
			filters={filterState.current}
		/>
	{/if}
</div>
