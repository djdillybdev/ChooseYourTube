<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import type { PageData } from './$types';
	import VideoList from '$lib/components/video/VideoList.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import ChannelContentTabs from '$lib/components/channel/ChannelContentTabs.svelte';
	import { createChannelMap } from '$lib/utils/channelLookup';
	import { formatRelativeDate } from '$lib/utils/formatDate';
	import { playFromPlaylist } from '$lib/stores/playerState.svelte';
	import type { SyncRunOut, VideoOut } from '$lib/types/api';
	import { openEditChannel } from '$lib/stores/modalState.svelte';
	import { api } from '$lib/api';
	import { onDestroy } from 'svelte';
	import { pollSyncRun } from '$lib/utils/syncPolling';
	import ChannelHeader from '$lib/components/channel/ChannelHeader.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	const channelMap = $derived(createChannelMap([data.channel]));
	let isRefreshing = $state(false);
	let refreshError = $state<string | null>(null);
	let activeRun = $state<SyncRunOut | null>(null);
	let cancelled = false;
	onDestroy(() => (cancelled = true));

	async function handlePlay(video: VideoOut): Promise<boolean> {
		return playFromPlaylist(data.playlist.id, video.id);
	}

	async function handleRefresh() {
		isRefreshing = true;
		refreshError = null;

		try {
			const run = await api.channels.refreshPlaylists(data.channel.id);
			activeRun = run;
			const completed = await pollSyncRun(
				run.id,
				(id) => api.syncRuns.get(id),
				(updated) => (activeRun = updated),
				() => cancelled
			);
			if (completed?.status === 'succeeded' || completed?.status === 'partial')
				await invalidateAll();
			if (completed?.status === 'failed') refreshError = completed.error_message;
		} catch (err) {
			refreshError = err instanceof Error ? err.message : 'Failed to refresh channel';
			console.error('Failed to refresh channel playlists:', err);
		} finally {
			isRefreshing = false;
		}
	}
</script>

<svelte:head>
	<title>{data.playlist.name} - {data.channel.title} - ChooseYourTube</title>
</svelte:head>

<div class="container mx-auto max-w-7xl px-4 py-6 sm:px-6">
	<ChannelHeader
		channel={data.channel}
		countLabel={`${data.total} videos in playlist`}
		updatedLabel={data.playlist.source_last_synced_at
			? `Synced ${formatRelativeDate(data.playlist.source_last_synced_at)}`
			: undefined}
		sync={activeRun ?? data.channel.latest_sync}
		syncAnnouncement={activeRun ? `Playlist refresh ${activeRun.status}` : ''}
		{refreshError}
		{isRefreshing}
		canRefresh={data.runtime.features.background_jobs}
		refreshDisabledReason="Live refresh is disabled in the demo."
		refreshLabel="Refresh playlist"
		onEdit={() => openEditChannel(data.channel)}
		onRefresh={handleRefresh}
	/>

	<ChannelContentTabs channelId={data.channel.id} active="playlists" />

	<div class="mb-4 rounded-box border border-base-300 bg-base-100 p-4">
		<div class="flex items-center justify-between gap-3">
			<div class="min-w-0">
				<h2 class="truncate text-xl font-semibold">{data.playlist.name}</h2>
				{#if data.playlist.description}
					<p class="mt-1 text-sm text-base-content/70">{data.playlist.description}</p>
				{/if}
			</div>
			{#if !data.playlist.source_is_active}
				<span class="badge badge-warning">Inactive</span>
			{/if}
		</div>
	</div>

	{#if data.videos.length > 0}
		<VideoList videos={data.videos} {channelMap} onPlay={handlePlay} showQueueActions={false} />
		<PaginationControls
			total={data.total}
			currentPage={data.page}
			pageSize={data.pageSize}
			basePath={`/channels/${data.channel.id}/playlists/${data.playlist.id}`}
		/>
	{:else}
		<EmptyState
			icon="video"
			title="No videos found"
			message="This playlist has no available videos."
		/>
	{/if}
</div>
