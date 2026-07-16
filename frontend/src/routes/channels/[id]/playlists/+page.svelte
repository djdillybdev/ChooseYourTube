<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import { resolve } from '$app/paths';
	import type { PageData } from './$types';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import ChannelContentTabs from '$lib/components/channel/ChannelContentTabs.svelte';
	import { formatRelativeDate } from '$lib/utils/formatDate';
	import { openEditChannel } from '$lib/stores/modalState.svelte';
	import { api } from '$lib/api';
	import { onDestroy } from 'svelte';
	import { pollSyncRun } from '$lib/utils/syncPolling';
	import type { SyncRunOut } from '$lib/types/api';
	import ChannelHeader from '$lib/components/channel/ChannelHeader.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let isRefreshing = $state(false);
	let refreshError = $state<string | null>(null);
	let activeRun = $state<SyncRunOut | null>(null);
	let cancelled = false;
	onDestroy(() => (cancelled = true));

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
	<title>{data.channel.title} Playlists - ChooseYourTube</title>
</svelte:head>

<div class="container mx-auto max-w-7xl px-4 py-6 sm:px-6">
	<ChannelHeader
		channel={data.channel}
		countLabel={`${data.total} playlists`}
		updatedLabel={data.channel.last_updated
			? `Updated ${formatRelativeDate(data.channel.last_updated)}`
			: undefined}
		sync={activeRun ?? data.channel.latest_sync}
		syncAnnouncement={activeRun ? `Playlist refresh ${activeRun.status}` : ''}
		{refreshError}
		{isRefreshing}
		canRefresh={data.runtime.features.background_jobs}
		refreshDisabledReason="Live refresh is disabled in the demo."
		refreshLabel="Refresh playlists"
		onEdit={() => openEditChannel(data.channel)}
		onRefresh={handleRefresh}
	/>

	<ChannelContentTabs channelId={data.channel.id} active="playlists" />

	{#if data.playlists.length > 0}
		<div class="space-y-3">
			{#each data.playlists as playlist (playlist.id)}
				<a
					href={resolve('/channels/[id]/playlists/[playlistId]', {
						id: data.channel.id,
						playlistId: playlist.id
					})}
					class="card border border-base-300 bg-base-100 transition-colors hover:border-primary"
				>
					<div class="card-body p-4">
						<div class="flex items-start gap-4">
							<div class="h-24 w-40 shrink-0 overflow-hidden rounded-box bg-base-200">
								{#if playlist.display_thumbnail_url}
									<img
										src={playlist.display_thumbnail_url}
										alt={playlist.name}
										class="h-full w-full object-cover"
									/>
								{:else}
									<div class="flex h-full w-full items-center justify-center text-base-content/40">
										<svg
											xmlns="http://www.w3.org/2000/svg"
											fill="none"
											viewBox="0 0 24 24"
											stroke-width="1.5"
											stroke="currentColor"
											class="h-8 w-8"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												d="M9 9l10.5-3m0 0L21 16.5M19.5 6L9 9m0 0l-1.5 10.5M9 9L3 7.5m4.5 12L3 7.5m0 0L13.5 4.5"
											/>
										</svg>
									</div>
								{/if}
							</div>
							<div class="min-w-0">
								<h2 class="truncate font-semibold">{playlist.name}</h2>
								<p class="text-sm text-base-content/60">
									{playlist.total_videos} videos
								</p>
								{#if playlist.description}
									<p class="mt-1 line-clamp-2 text-sm text-base-content/70">
										{playlist.description}
									</p>
								{/if}
							</div>
							<div class="ml-auto">
								{#if !playlist.source_is_active}
									<span class="badge badge-sm badge-warning">Inactive</span>
								{/if}
							</div>
						</div>
					</div>
				</a>
			{/each}
		</div>

		<PaginationControls
			total={data.total}
			currentPage={data.page}
			pageSize={data.pageSize}
			basePath={`/channels/${data.channel.id}/playlists`}
		/>
	{:else}
		<EmptyState
			icon="folder"
			title="No playlists found"
			message="This channel has no synced playlists yet."
		/>
	{/if}
</div>
