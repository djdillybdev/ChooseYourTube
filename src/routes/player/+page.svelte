<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { playerState, closePlayer, initializeQueue } from '$lib/stores/playerState.svelte';
	import { openSaveVideo } from '$lib/stores/modalState.svelte';
	import YouTubePlayer from '$lib/components/player/YouTubePlayer.svelte';
	import QueueList from '$lib/components/player/QueueList.svelte';
	import { createChannelMap, getChannelTitle } from '$lib/utils/channelLookup';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Access parent layout data
	const channels = $derived((data as any).channels ?? []);
	const channelMap = $derived(channels.length > 0 ? createChannelMap(channels) : undefined);
	const currentVideoId = $derived(playerState.current.currentVideo?.id ?? null);

	let showQueue = $state(false);
	let showDescription = $state(false);
	let returnUrl = $state('/inbox');

	$effect(() => {
		currentVideoId;
		showDescription = false;
	});

	onMount(() => {
		returnUrl = new URLSearchParams(window.location.search).get('return') ?? '/inbox';

		void initializeQueue().then(() => {
			if (!playerState.current.currentVideo && playerState.current.queue.length === 0) {
				goto(returnUrl, { replaceState: true });
			}
		});

		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') goto(returnUrl);
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});

	function handleBack() {
		goto(returnUrl);
	}
	function handleClose() {
		void closePlayer();
	}
</script>

<svelte:head>
	<title>{playerState.current.currentVideo?.title ?? 'Player'} – ChooseYourTube</title>
</svelte:head>

<!-- Full-viewport overlay – covers sidebar rendered by root layout -->
<div class="fixed inset-0 z-50 flex flex-col bg-base-100">
	<!-- Header -->
	<header
		class="flex shrink-0 items-center justify-between border-b border-base-300 bg-base-100 px-6 py-2"
	>
		<button
			class="flex items-center gap-2 text-sm text-base-content/70 transition-colors hover:text-base-content"
			onclick={handleBack}
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
				class="h-4 w-4"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
				/>
			</svg>
			Back
		</button>

		<div class="flex items-center gap-2">
			<button
				class="btn btn-ghost btn-sm"
				onclick={() => playerState.current.currentVideo && openSaveVideo(playerState.current.currentVideo)}
				disabled={!playerState.current.currentVideo}
			>
				Save
			</button>
			<button
				class="btn btn-ghost btn-sm"
				class:btn-active={showQueue}
				onclick={() => (showQueue = !showQueue)}
			>
				Queue
				<span class="badge badge-sm badge-primary">{playerState.current.queue.length}</span>
			</button>
			<button
				class="btn btn-square btn-ghost btn-sm"
				onclick={handleClose}
				aria-label="Close player"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					class="h-5 w-5"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>
	</header>

	{#if !playerState.current.isQueueReady && playerState.current.isQueueSyncing}
		<div class="flex min-h-0 flex-1 items-center justify-center bg-base-200 p-6">
			<div class="flex items-center gap-3 text-sm text-base-content/70">
				<span class="loading loading-md loading-spinner"></span>
				Loading queue...
			</div>
		</div>
	{:else}
		<!-- Video area with optional right queue panel -->
		<div class="relative z-0 flex min-h-0 flex-1 overflow-hidden bg-base-200 p-6">
			<div class="flex min-h-0 w-full flex-col gap-4 lg:flex-row lg:items-start lg:justify-center">
				<div class="flex min-h-0 flex-1 items-center justify-center">
					<div class="aspect-video w-full max-w-4xl">
						{#key playerState.current.currentVideo?.id}
							<YouTubePlayer />
						{/key}
					</div>
				</div>

				{#if showQueue}
					<aside
						class="flex min-h-0 w-full shrink-0 overflow-hidden rounded-lg border border-base-300 bg-base-100 lg:w-96"
						aria-label="Queue panel"
					>
						<QueueList {channelMap} />
					</aside>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Bottom panel -->
	<div class="relative z-20 shrink-0 border-t border-base-300 bg-base-100">
		<!-- Video info -->
		<div class="px-6 pt-4 pb-4">
			<h2 class="text-lg font-semibold text-base-content">
				{playerState.current.currentVideo?.title}
			</h2>
			<p class="text-sm text-base-content/60">
				{#if channelMap && playerState.current.currentVideo}
					{getChannelTitle(playerState.current.currentVideo.channel_id, channelMap)}
				{:else}
					{playerState.current.currentVideo?.channel_id}
				{/if}
			</p>

			<div class="mt-3">
				<button
					class="btn btn-ghost btn-xs"
					onclick={() => (showDescription = !showDescription)}
					aria-expanded={showDescription}
					aria-controls="video-description-panel"
				>
					{showDescription ? 'Hide description' : 'Show description'}
				</button>

				{#if showDescription}
					<div
						id="video-description-panel"
						class="mt-2 max-h-40 overflow-y-auto rounded-md bg-base-200 px-3 py-2 text-sm text-base-content/80"
					>
						{#if playerState.current.currentVideo?.description}
							<p class="break-words whitespace-pre-wrap">
								{playerState.current.currentVideo.description}
							</p>
						{:else}
							<p class="text-base-content/60 italic">No description available.</p>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
