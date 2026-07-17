<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import QueueList from '$lib/components/player/QueueList.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import { initializeQueue, playerState } from '$lib/stores/playerState.svelte';
	import { createChannelMap } from '$lib/utils/channelLookup';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	const channelMap = $derived(createChannelMap(data.channels ?? []));

	onMount(() => {
		void initializeQueue(playerState.current.queueMode !== 'system');
	});

	async function openPlayer() {
		await goto(resolve('/player?return=%2Fqueue' as '/player'));
	}
</script>

<svelte:head>
	<title>Queue - ChooseYourTube</title>
	<meta name="description" content="Review and manage your ChooseYourTube playback queue." />
</svelte:head>

<div class="container mx-auto max-w-5xl px-4 py-6 sm:px-6">
	<PageHeader
		title="Queue"
		description={`${playerState.current.queue.length} ${playerState.current.queue.length === 1 ? 'video' : 'videos'}`}
	/>

	{#if !playerState.current.isQueueReady && playerState.current.isQueueSyncing}
		<div
			class="flex items-center justify-center rounded-box border border-base-300 bg-base-100 p-10"
		>
			<span class="loading loading-md loading-spinner" aria-hidden="true"></span>
			<span class="ml-3 text-sm text-base-content/70">Loading queue...</span>
		</div>
	{:else}
		<QueueList {channelMap} variant="page" onPlaybackStarted={openPlayer} />
	{/if}
</div>
