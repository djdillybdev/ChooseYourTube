<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { goto, invalidateAll } from '$app/navigation';
	import { resolve } from '$app/paths';
	import type { PageData } from './$types';
	import VideoList from '$lib/components/video/VideoList.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import SearchBar from '$lib/components/ui/SearchBar.svelte';
	import { formatRelativeDate } from '$lib/utils/formatDate';
	import { uiState } from '$lib/stores/uiState.svelte';
	import { api } from '$lib/api';
	import { openEditChannel } from '$lib/stores/modalState.svelte';
	import { createChannelMap } from '$lib/utils/channelLookup';
	import ChannelContentTabs from '$lib/components/channel/ChannelContentTabs.svelte';
	import { pollSyncRun } from '$lib/utils/syncPolling';
	import type { SyncRunOut } from '$lib/types/api';
	import { actionStatus } from '$lib/stores/actionStatus.svelte';
	import ChannelHeader from '$lib/components/channel/ChannelHeader.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Create map from the single channel we loaded
	const channelMap = $derived(createChannelMap([data.channel]));

	let isRefreshing = $state(false);
	let refreshError = $state<string | null>(null);
	let activeRun = $state<SyncRunOut | null>(null);
	let pollingCancelled = false;
	onDestroy(() => (pollingCancelled = true));

	async function handleRefresh() {
		isRefreshing = true;
		refreshError = null;

		try {
			const run = await api.channels.refresh(data.channel.id);
			activeRun = run;
			const completed = await pollSyncRun(
				run.id,
				(id) => api.syncRuns.get(id),
				(updated) => (activeRun = updated),
				() => pollingCancelled
			);
			if (completed?.status === 'succeeded' || completed?.status === 'partial') {
				await invalidateAll();
				actionStatus.announce(
					completed.status === 'succeeded'
						? `${data.channel.title} synchronized.`
						: `${data.channel.title} synchronized with some items skipped.`
				);
			}
			if (completed?.status === 'failed') refreshError = completed.error_message;
		} catch (err) {
			refreshError = err instanceof Error ? err.message : 'Failed to refresh channel';
			console.error('Failed to refresh channel:', err);
		} finally {
			isRefreshing = false;
		}
	}

	/**
	 * Sync the persisted pageSize preference into the URL on first visit.
	 * Uses replaceState so it doesn't pollute history.
	 */
	onMount(() => {
		const url = new URL(window.location.href);
		if (!url.searchParams.has('pageSize')) {
			url.searchParams.set('pageSize', String(uiState.current.pageSize));
			if (!url.searchParams.has('page')) url.searchParams.set('page', '1');
			const channelPath = resolve('/channels/[id]', { id: data.channel.id });
			goto(resolve(`${channelPath}${url.search}` as '/inbox'), {
				replaceState: true
			});
		}
	});
</script>

<svelte:head>
	<title>{data.channel.title} - ChooseYourTube</title>
	<meta
		name="description"
		content={`Browse saved videos and synchronization status for ${data.channel.title}.`}
	/>
</svelte:head>

<div class="container mx-auto max-w-7xl px-4 py-6 sm:px-6">
	<ChannelHeader
		channel={data.channel}
		countLabel={`${data.total} videos`}
		updatedLabel={data.channel.last_updated
			? `Updated ${formatRelativeDate(data.channel.last_updated)}`
			: undefined}
		sync={activeRun ?? data.channel.latest_sync}
		syncAnnouncement={activeRun ? `Refresh ${activeRun.status}` : ''}
		{refreshError}
		{isRefreshing}
		canRefresh={data.runtime.features.background_jobs}
		refreshDisabledReason="Live refresh is disabled in the demo; data is maintained daily."
		showFavorite
		onEdit={() => openEditChannel(data.channel)}
		onRefresh={handleRefresh}
	/>

	<ChannelContentTabs channelId={data.channel.id} active="videos" />

	<!-- Search bar -->
	<div class="mb-4">
		<SearchBar
			basePath="/channels/{data.channel.id}"
			initialValue={data.q}
			placeholder="Search in {data.channel.title}..."
		/>
	</div>

	<!-- Videos List -->
	{#if data.videos.length > 0}
		<VideoList videos={data.videos} {channelMap} />
		<PaginationControls
			total={data.total}
			currentPage={data.page}
			pageSize={data.pageSize}
			basePath={`/channels/${data.channel.id}`}
		/>
	{:else}
		<EmptyState
			icon={data.q ? 'search' : 'video'}
			title="No videos found"
			message={data.q
				? `No results for "${data.q}". Try a different search term.`
				: 'Try adjusting filters or refreshing the channel to fetch new videos'}
		/>
	{/if}
</div>
