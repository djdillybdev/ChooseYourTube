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
	const channelMap = $derived(createChannelMap(data.channels));
</script>

<svelte:head><title>Favorites - ChooseYourTube</title></svelte:head>

<div class="container mx-auto max-w-7xl p-6">
	<div class="mb-6">
		<div class="mb-2 flex items-center gap-3">
			<svg
				viewBox="0 0 24 24"
				fill="currentColor"
				stroke="currentColor"
				class="h-8 w-8 text-warning"
				aria-hidden="true"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="1.5"
					d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
				/>
			</svg>
			<h1 class="text-3xl font-bold">Favorites</h1>
		</div>
		<p class="text-base-content/60">
			{data.channels.length}
			{data.channels.length === 1 ? 'channel' : 'channels'}
			{#if data.total > 0}· {data.total} {data.total === 1 ? 'video' : 'videos'}{/if}
		</p>
	</div>

	{#if data.channels.length > 0}
		<section class="mb-8">
			<h2 class="mb-4 text-xl font-semibold">Channels</h2>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				{#each data.channels as channel (channel.id)}
					<ChannelCard {channel} backgroundJobsEnabled={data.runtime.features.background_jobs} />
				{/each}
			</div>
		</section>
	{/if}

	<section>
		<h2 class="mb-4 text-xl font-semibold">Videos</h2>
		<div class="mb-4">
			<SearchBar basePath="/favorites" initialValue={data.q} placeholder="Search favorites..." />
		</div>
		{#if data.videos.length > 0}
			<VideoList videos={data.videos} {channelMap} />
			<PaginationControls
				total={data.total}
				currentPage={data.page}
				pageSize={data.pageSize}
				basePath="/favorites"
			/>
		{:else if data.q}
			<EmptyState icon="search" title="No videos found" message={`No results for "${data.q}".`} />
		{:else if data.channels.length === 0}
			<EmptyState
				icon="folder"
				title="No favorite channels"
				message="Favorite a channel to add it here"
			/>
		{:else}
			<EmptyState
				icon="video"
				title="No videos yet"
				message="Refresh your favorite channels to fetch videos"
			/>
		{/if}
	</section>
</div>
