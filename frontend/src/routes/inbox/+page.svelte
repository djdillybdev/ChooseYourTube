<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	import VideoList from '$lib/components/video/VideoList.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import ErrorState from '$lib/components/ui/ErrorState.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import SearchBar from '$lib/components/ui/SearchBar.svelte';
	import { uiState, setPageSize } from '$lib/stores/uiState.svelte';
	import { createChannelMap } from '$lib/utils/channelLookup';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	// Access parent layout data (SvelteKit merges layout + page data)
	const channels = $derived((data as any).channels ?? []);
	const channelMap = $derived(channels.length > 0 ? createChannelMap(channels) : undefined);

	/**
	 * Sync the persisted pageSize preference into the URL on first visit.
	 * Uses replaceState so it doesn't pollute history.
	 */
	onMount(() => {
		const url = new URL(window.location.href);
		if (!url.searchParams.has('pageSize')) {
			url.searchParams.set('pageSize', String(uiState.current.pageSize));
			if (!url.searchParams.has('page')) url.searchParams.set('page', '1');
			goto(url.pathname + url.search, { replaceState: true });
		} else {
			// Update stored preference when URL has pageSize
			setPageSize(data.pageSize);
		}
	});
</script>

<div class="container mx-auto max-w-4xl p-6">
	<div class="mb-6">
		<h1 class="text-2xl font-bold">Inbox</h1>
		<p class="text-sm text-base-content/60">
			{data.total}
			{data.total === 1 ? 'video' : 'videos'}
		</p>
	</div>

	<!-- Search bar -->
	<div class="mb-4">
		<SearchBar basePath="/inbox" initialValue={data.q} placeholder="Search unwatched videos..." />
	</div>

	{#if data.error}
		<ErrorState message={data.error} />
	{:else if data.videos.length === 0}
		<EmptyState
			icon={data.q ? 'search' : 'video'}
			title="No videos found"
			message={data.q
				? `No results for "${data.q}". Try a different search term.`
				: 'No unwatched videos. Check back later or adjust your subscriptions!'}
		/>
	{:else}
		<VideoList videos={data.videos} {channelMap} />

		<PaginationControls
			total={data.total}
			currentPage={data.page}
			pageSize={data.pageSize}
			basePath="/inbox"
		/>
	{/if}
</div>
