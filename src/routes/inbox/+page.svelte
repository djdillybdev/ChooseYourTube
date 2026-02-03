<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	import VideoList from '$lib/components/video/VideoList.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import ErrorState from '$lib/components/ui/ErrorState.svelte';
	import { uiState, setPageSize } from '$lib/stores/uiState.svelte';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

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

	/** Keep the persisted preference in sync when pageSize changes via the dropdown */
	$effect(() => {
		setPageSize(data.pageSize);
	});
</script>

<div class="container mx-auto max-w-4xl p-6">
	<div class="mb-6">
		<h1 class="text-2xl font-bold">Inbox</h1>
		<p class="text-sm text-base-content/60">
			{data.total} {data.total === 1 ? 'video' : 'videos'}
		</p>
	</div>

	{#if data.error}
		<ErrorState message={data.error} />
	{:else}
		<VideoList videos={data.videos} />

		<PaginationControls
			total={data.total}
			currentPage={data.page}
			pageSize={data.pageSize}
			basePath="/inbox"
		/>
	{/if}
</div>
