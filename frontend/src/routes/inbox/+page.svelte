<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import type { PageData } from './$types';
	import VideoList from '$lib/components/video/VideoList.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import ErrorState from '$lib/components/ui/ErrorState.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import SearchBar from '$lib/components/ui/SearchBar.svelte';
	import { uiState, setPageSize } from '$lib/stores/uiState.svelte';
	import { createChannelMap } from '$lib/utils/channelLookup';
	import { openAddChannel } from '$lib/stores/modalState.svelte';
	import { invalidateAll } from '$app/navigation';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	// Access parent layout data (SvelteKit merges layout + page data)
	const channels = $derived(data.channels ?? []);
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
			goto(resolve(`/inbox${url.search}` as '/inbox'), { replaceState: true });
		} else {
			// Update stored preference when URL has pageSize
			setPageSize(data.pageSize);
		}
	});
</script>

<svelte:head>
	<title>Inbox - ChooseYourTube</title>
	<meta name="description" content="Browse recent videos from the channels you follow." />
</svelte:head>

<div class="container mx-auto max-w-5xl px-4 py-6 sm:px-6">
	<PageHeader
		title="Inbox"
		description={`${data.total} ${data.total === 1 ? 'video' : 'videos'}`}
	/>

	<!-- Search bar -->
	<div class="mb-4">
		<SearchBar basePath="/inbox" initialValue={data.q} placeholder="Search unwatched videos..." />
	</div>

	{#if data.error}
		<ErrorState
			heading="Videos could not be loaded"
			message={data.error}
			onRetry={() => invalidateAll()}
		/>
	{:else if data.videos.length === 0}
		<EmptyState
			icon={data.q ? 'search' : channels.length === 0 ? 'inbox' : 'video'}
			title={data.q
				? 'No matching videos'
				: channels.length === 0
					? 'Follow your first channel'
					: 'No new standard videos'}
			message={data.q
				? `No results for "${data.q}". Try a different search term or reset filters.`
				: channels.length === 0
					? 'Choose a YouTube channel you value. Its latest public videos will appear here after synchronization.'
					: 'Your followed channels may still be synchronizing, or you have watched everything currently in the Inbox.'}
			actionLabel={channels.length === 0 ? 'Follow a channel' : undefined}
			onAction={channels.length === 0 ? openAddChannel : undefined}
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
