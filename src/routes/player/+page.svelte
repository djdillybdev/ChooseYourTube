<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { playerState, closePlayer } from '$lib/stores/playerState.svelte';
	import YouTubePlayer from '$lib/components/player/YouTubePlayer.svelte';
	import PlayerControls from '$lib/components/player/PlayerControls.svelte';
	import QueueList from '$lib/components/player/QueueList.svelte';

	let showQueue = $state(false);
	let returnUrl = $state('/inbox');

	onMount(() => {
		returnUrl = new URLSearchParams(window.location.search).get('return') ?? '/inbox';

		if (!playerState.current.currentVideo) {
			goto(returnUrl, { replaceState: true });
			return;
		}

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
		closePlayer();
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

	<!-- Video (fills remaining height, centred) -->
	<div class="flex min-h-0 flex-1 items-center justify-center bg-base-200 p-6">
		<div class="aspect-video w-full max-w-4xl">
			<YouTubePlayer />
		</div>
	</div>

	<!-- Bottom panel -->
	<div class="shrink-0 border-t border-base-300 bg-base-100">
		<!-- Video info -->
		<div class="px-6 pt-4 pb-1">
			<h2 class="text-lg font-semibold text-base-content">
				{playerState.current.currentVideo?.title}
			</h2>
			<p class="text-sm text-base-content/60">
				{playerState.current.currentVideo?.channel_id}
			</p>
		</div>

		<!-- Playback controls -->
		<div class="px-6 pb-3">
			<PlayerControls onToggleQueue={() => (showQueue = !showQueue)} {showQueue} />
		</div>

		<!-- Queue (collapsible) -->
		{#if showQueue}
			<div class="max-h-64 overflow-y-auto border-t border-base-300">
				<QueueList />
			</div>
		{/if}
	</div>
</div>
