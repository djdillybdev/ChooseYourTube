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
	import SyncStatus from '$lib/components/channel/SyncStatus.svelte';

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

<div class="container mx-auto max-w-7xl p-6">
	<div class="mb-6">
		<div class="mb-4 flex items-start gap-6">
			{#if data.channel.thumbnail_url}
				<img
					src={data.channel.thumbnail_url}
					alt={data.channel.title}
					class="h-24 w-24 rounded-full object-cover"
				/>
			{:else}
				<div class="flex h-24 w-24 items-center justify-center rounded-full bg-base-300">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="h-12 w-12 text-base-content/40"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z"
						/>
					</svg>
				</div>
			{/if}

			<div class="min-w-0 flex-1">
				<h1 class="mb-1 text-3xl font-bold">{data.channel.title}</h1>
				<p class="mb-2 text-base-content/60">@{data.channel.handle}</p>
				<div class="flex items-center gap-4 text-sm text-base-content/60">
					<span>{data.total} playlists</span>
					{#if data.channel.last_updated}
						<span>Updated {formatRelativeDate(data.channel.last_updated)}</span>
					{/if}
				</div>
				{#if refreshError}
					<div class="mt-2 text-sm text-error">{refreshError}</div>
				{/if}
				<div class="mt-2"><SyncStatus sync={activeRun ?? data.channel.latest_sync} /></div>
				<div class="sr-only" aria-live="polite">
					{activeRun ? `Playlist refresh ${activeRun.status}` : ''}
				</div>
			</div>

			<div class="flex items-center gap-2">
				<button
					class="btn btn-square btn-ghost btn-sm"
					onclick={() => openEditChannel(data.channel)}
					aria-label="Edit channel"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="h-5 w-5"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
						/>
					</svg>
				</button>
				<button
					class="btn gap-2 btn-primary"
					onclick={handleRefresh}
					disabled={isRefreshing || !data.runtime.features.background_jobs}
					title={data.runtime.features.background_jobs
						? 'Refresh channel playlists'
						: 'Live refresh is disabled in the recruiter demo'}
				>
					{#if isRefreshing}
						<span class="loading loading-sm loading-spinner"></span>
						Refreshing...
					{:else}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="h-5 w-5"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
							/>
						</svg>
						Refresh
					{/if}
				</button>
			</div>
		</div>
	</div>

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
