<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
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
	import { api } from '$lib/api';
	import { actionStatus } from '$lib/stores/actionStatus.svelte';
	import type { BulkChannelRefreshItemOut, SyncRunStatus } from '$lib/types/api';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	// Access parent layout data (SvelteKit merges layout + page data)
	const channels = $derived(data.channels ?? []);
	const channelMap = $derived(channels.length > 0 ? createChannelMap(channels) : undefined);
	const backgroundJobsEnabled = $derived(data.runtime.features.background_jobs);

	let isRefreshingAll = $state(false);
	let refreshAllError = $state<string | null>(null);
	let refreshAllTotal = $state(0);
	let refreshAllCompleted = $state(0);
	let refreshPollingCancelled = false;
	const terminalStatuses = new Set<SyncRunStatus>(['succeeded', 'partial', 'failed']);
	const refreshPollDelays = [1000, 2000, 4000, 8000, 10000];

	onDestroy(() => (refreshPollingCancelled = true));

	function updateTrackedStatuses(statuses: Map<string, SyncRunStatus>) {
		for (const channel of channels) {
			const sync = channel.latest_sync;
			if (sync && statuses.has(sync.id)) statuses.set(sync.id, sync.status);
		}
		refreshAllCompleted = [...statuses.values()].filter((status) =>
			terminalStatuses.has(status)
		).length;
	}

	function finalRefreshMessage(
		items: BulkChannelRefreshItemOut[],
		statuses: Map<string, SyncRunStatus>
	) {
		const failed = items.filter((item) => statuses.get(item.sync_run_id) === 'failed').length;
		const completed = items.length - failed;
		if (failed === 0)
			return `${completed} ${completed === 1 ? 'channel' : 'channels'} synchronized.`;
		return `${completed} ${completed === 1 ? 'channel' : 'channels'} synchronized; ${failed} failed.`;
	}

	async function handleRefreshAll() {
		isRefreshingAll = true;
		refreshAllError = null;
		refreshPollingCancelled = false;
		refreshAllCompleted = 0;

		try {
			const batch = await api.channels.refreshAll();
			refreshAllTotal = batch.total_channels;
			if (batch.total_channels === 0) {
				actionStatus.announce('There are no channels to refresh.');
				return;
			}

			const statuses = new Map(batch.items.map((item) => [item.sync_run_id, item.status] as const));
			updateTrackedStatuses(statuses);
			actionStatus.announce(
				`Refresh queued for ${batch.total_channels} ${batch.total_channels === 1 ? 'channel' : 'channels'}.`
			);

			let attempt = 0;
			while (
				!refreshPollingCancelled &&
				[...statuses.values()].some((status) => !terminalStatuses.has(status))
			) {
				await new Promise((resolve) =>
					setTimeout(resolve, refreshPollDelays[Math.min(attempt, refreshPollDelays.length - 1)])
				);
				if (refreshPollingCancelled) return;
				await invalidateAll();
				updateTrackedStatuses(statuses);
				attempt += 1;
			}

			if (!refreshPollingCancelled) {
				actionStatus.announce(finalRefreshMessage(batch.items, statuses), 6000);
			}
		} catch (error) {
			refreshAllError = error instanceof Error ? error.message : 'Failed to refresh channels';
			console.error('Failed to refresh all channels:', error);
		} finally {
			if (!refreshPollingCancelled) isRefreshingAll = false;
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
			goto(resolve(`/inbox${url.search}` as '/inbox'), { replaceState: true });
		} else {
			// Update stored preference when URL has pageSize
			setPageSize(data.pageSize);
		}
	});
</script>

{#snippet headerActions()}
	<button
		type="button"
		class="btn btn-outline btn-sm"
		disabled={!backgroundJobsEnabled || channels.length === 0 || isRefreshingAll}
		title={!backgroundJobsEnabled
			? 'Live refresh is disabled in the demo; data is maintained daily.'
			: channels.length === 0
				? 'Follow a channel to refresh your Inbox'
				: 'Refresh all followed channels'}
		onclick={handleRefreshAll}
	>
		{#if isRefreshingAll}<span class="loading loading-sm loading-spinner" aria-hidden="true"
			></span>{/if}
		{isRefreshingAll ? `Refreshing ${refreshAllCompleted}/${refreshAllTotal}…` : 'Refresh all'}
	</button>
{/snippet}

<svelte:head>
	<title>Inbox - ChooseYourTube</title>
	<meta name="description" content="Browse recent videos from the channels you follow." />
</svelte:head>

<div class="container mx-auto max-w-5xl px-4 py-6 sm:px-6">
	<PageHeader
		title="Inbox"
		description={`${data.total} ${data.total === 1 ? 'video' : 'videos'}`}
		actions={headerActions}
	/>
	{#if refreshAllError}<p class="mb-4 text-sm text-error" role="alert">{refreshAllError}</p>{/if}

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
