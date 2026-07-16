<script lang="ts">
	import type { PageData } from './$types';
	import ChannelCard from '$lib/components/channel/ChannelCard.svelte';
	import VideoList from '$lib/components/video/VideoList.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import SearchBar from '$lib/components/ui/SearchBar.svelte';
	import { openEditCategory } from '$lib/stores/modalState.svelte';
	import { createChannelMap } from '$lib/utils/channelLookup';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();
	const channelMap = $derived(createChannelMap(data.channels));
</script>

<svelte:head><title>{data.category.name} - ChooseYourTube</title></svelte:head>

<div class="container mx-auto max-w-7xl px-4 py-6 sm:px-6">
	<div class="mb-6 flex items-start justify-between gap-4">
		<div>
			<div class="mb-2 flex items-center gap-3">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-8 w-8 text-primary">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="1.5"
						d="M4.5 6.75h15M4.5 12h15m-15 5.25h15"
					/>
				</svg>
				<h1 class="text-3xl font-bold">{data.category.name}</h1>
			</div>
			<p class="text-base-content/60">
				{data.channels.length}
				{data.channels.length === 1 ? 'channel' : 'channels'}
				{#if data.total > 0}· {data.total} {data.total === 1 ? 'video' : 'videos'}{/if}
			</p>
		</div>
		<button
			class="btn btn-square btn-ghost btn-sm"
			onclick={() => openEditCategory(data.category)}
			aria-label="Edit category"
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="1.5"
					d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z"
				/>
			</svg>
		</button>
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
			<SearchBar
				basePath="/categories/{data.category.id}"
				initialValue={data.q}
				placeholder="Search in category..."
			/>
		</div>
		{#if data.videos.length > 0}
			<VideoList videos={data.videos} {channelMap} />
			<PaginationControls
				total={data.total}
				currentPage={data.page}
				pageSize={data.pageSize}
				basePath={`/categories/${data.category.id}`}
			/>
		{:else if data.q}
			<EmptyState icon="search" title="No videos found" message={`No results for "${data.q}".`} />
		{:else if data.channels.length === 0}
			<EmptyState
				icon="folder"
				title="No channels in this category"
				message="Add channels to this category to see their videos here"
			/>
		{:else}
			<EmptyState
				icon="video"
				title="No videos yet"
				message="Refresh your channels to fetch videos"
			/>
		{/if}
	</section>
</div>
