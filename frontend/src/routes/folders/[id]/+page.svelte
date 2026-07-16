<script lang="ts">
	import type { PageData } from './$types';
	import ChannelCard from '$lib/components/channel/ChannelCard.svelte';
	import VideoList from '$lib/components/video/VideoList.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import SearchBar from '$lib/components/ui/SearchBar.svelte';
	import { createChannelMap } from '$lib/utils/channelLookup';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Create map from channels in this folder
	const channelMap = $derived(createChannelMap(data.channels));
</script>

<svelte:head>
	<title>{data.folder.name} - ChooseYourTube</title>
</svelte:head>

<div class="container mx-auto max-w-7xl px-4 py-6 sm:px-6">
	<!-- Folder Header -->
	<div class="mb-6">
		<div class="flex items-start justify-between gap-4">
			<!-- Left: Folder info -->
			<div>
				<div class="mb-2 flex items-center gap-3">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="h-8 w-8 text-primary"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
						/>
					</svg>
					<h1 class="text-3xl font-bold">{data.folder.name}</h1>
				</div>
				<p class="text-base-content/60">
					{data.channels.length}
					{data.channels.length === 1 ? 'channel' : 'channels'}
					{#if data.total > 0}
						· {data.total} {data.total === 1 ? 'video' : 'videos'}
					{/if}
				</p>
			</div>
		</div>
	</div>

	<!-- Channels Section -->
	{#if data.channels.length > 0}
		<div class="mb-8">
			<h2 class="mb-4 text-xl font-semibold">Channels</h2>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				{#each data.channels as channel (channel.id)}
					<ChannelCard {channel} backgroundJobsEnabled={data.runtime.features.background_jobs} />
				{/each}
			</div>
		</div>
	{/if}

	<!-- Videos Section -->
	<div>
		<h2 class="mb-4 text-xl font-semibold">Videos</h2>

		<!-- Search bar -->
		<div class="mb-4">
			<SearchBar
				basePath="/folders/{data.folder.id}"
				initialValue={data.q}
				placeholder="Search in folder..."
			/>
		</div>

		{#if data.videos.length > 0}
			<VideoList videos={data.videos} {channelMap} />
			<PaginationControls
				total={data.total}
				currentPage={data.page}
				pageSize={data.pageSize}
				basePath={`/folders/${data.folder.id}`}
			/>
		{:else if data.q}
			<EmptyState
				icon="search"
				title="No videos found"
				message={`No results for "${data.q}". Try a different search term.`}
			/>
		{:else if data.channels.length === 0}
			<EmptyState
				icon="folder"
				title="No channels in this folder"
				message="Add channels to this folder to see their videos here"
			/>
		{:else}
			<EmptyState
				icon="video"
				title="No videos yet"
				message="Refresh your channels to fetch new videos"
			/>
		{/if}
	</div>
</div>
