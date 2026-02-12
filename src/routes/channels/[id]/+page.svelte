<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	import VideoList from '$lib/components/video/VideoList.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import { filterState } from '$lib/stores/filterState.svelte';
	import { formatRelativeDate } from '$lib/utils/formatDate';
	import { uiState } from '$lib/stores/uiState.svelte';
	import { api } from '$lib/api';
	import { openEditChannel } from '$lib/stores/modalState.svelte';
	import { createChannelMap } from '$lib/utils/channelLookup';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Create map from the single channel we loaded
	const channelMap = $derived(createChannelMap([data.channel]));

	let isRefreshing = $state(false);
	let refreshError = $state<string | null>(null);

	async function handleRefresh() {
		isRefreshing = true;
		refreshError = null;

		try {
			await api.channels.refresh(data.channel.id);
			// Ideally we'd invalidate the page data here to refetch
			// For now, just show success
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
			goto(url.pathname + url.search, { replaceState: true });
		}
	});
</script>

<svelte:head>
	<title>{data.channel.title} - ChooseYourTube</title>
</svelte:head>

<div class="container mx-auto max-w-7xl p-6">
	<!-- Channel Header -->
	<div class="mb-6">
		<div class="mb-4 flex items-start gap-6">
			<!-- Channel Thumbnail -->
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

			<!-- Channel Info -->
			<div class="min-w-0 flex-1">
				<h1 class="mb-1 text-3xl font-bold">{data.channel.title}</h1>
				<p class="mb-2 text-base-content/60">@{data.channel.handle}</p>

				<div class="flex items-center gap-4 text-sm text-base-content/60">
					<span>{data.total} videos</span>
					{#if data.channel.last_updated}
						<span>Updated {formatRelativeDate(data.channel.last_updated)}</span>
					{/if}
				</div>

				{#if refreshError}
					<div class="mt-2 text-sm text-error">{refreshError}</div>
				{/if}
			</div>

			<!-- Action buttons: Edit + Refresh -->
			<div class="flex items-center gap-2">
				<button
					class="btn btn-ghost btn-sm btn-square"
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

				<button class="btn gap-2 btn-primary" onclick={handleRefresh} disabled={isRefreshing}>
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

	<!-- Filter Toggle -->
	<div class="mb-4 flex items-center gap-2">
		<span class="text-sm font-medium">Filter:</span>
		<div class="btn-group">
			<button
				class="btn btn-sm"
				class:btn-active={filterState.current.is_watched === undefined}
				onclick={() => {
					filterState.update((state) => ({ ...state, is_watched: undefined }));
				}}
			>
				All
			</button>
			<button
				class="btn btn-sm"
				class:btn-active={filterState.current.is_watched === false}
				onclick={() => {
					filterState.update((state) => ({ ...state, is_watched: false }));
				}}
			>
				Unwatched
			</button>
			<button
				class="btn btn-sm"
				class:btn-active={filterState.current.is_watched === true}
				onclick={() => {
					filterState.update((state) => ({ ...state, is_watched: true }));
				}}
			>
				Watched
			</button>
		</div>
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
			icon="video"
			title="No videos found"
			message={filterState.current.is_watched !== undefined
				? 'Try changing the filter'
				: 'Refresh the channel to fetch new videos'}
		/>
	{/if}
</div>
