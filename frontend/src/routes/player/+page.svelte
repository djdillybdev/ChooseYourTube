<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { playerState, initializeQueue } from '$lib/stores/playerState.svelte';
	import { openSaveVideo } from '$lib/stores/modalState.svelte';
	import YouTubePlayer from '$lib/components/player/YouTubePlayer.svelte';
	import QueueList from '$lib/components/player/QueueList.svelte';
	import { createChannelMap, getChannelTitle } from '$lib/utils/channelLookup';
	import { fit16x9 } from '$lib/utils/playerFrameFit';
	import type { PageData } from './$types';
	import WatchLaterButton from '$lib/components/video/WatchLaterButton.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Access parent layout data
	const channels = $derived(data.channels ?? []);
	const channelMap = $derived(channels.length > 0 ? createChannelMap(channels) : undefined);
	const currentVideoId = $derived(playerState.current.currentVideo?.id ?? null);

	let showQueue = $state(false);
	let showDescription = $state(false);
	let returnUrl = $state('/inbox');
	let playerStageEl = $state<HTMLDivElement | null>(null);
	let frameWidth = $state(0);
	let frameHeight = $state(0);
	let stageResizeObserver: ResizeObserver | null = null;

	const DESKTOP_BREAKPOINT = 1024;
	const MOBILE_WIDTH_RATIO = 0.9;
	const MOBILE_MAX_WIDTH = 1600;
	const DESKTOP_MAX_WIDTH = 1400;
	const DESKTOP_WIDTH_RATIO = 0.96;
	const QUEUE_RESERVED_REM = 24;
	const QUEUE_GAP_PX = 16;

	function getRootFontSizePx(): number {
		if (typeof window === 'undefined') return 16;
		const value = Number.parseFloat(getComputedStyle(document.documentElement).fontSize);
		return Number.isFinite(value) ? value : 16;
	}

	function getMaxFrameWidth(viewportWidth: number): number {
		if (viewportWidth < DESKTOP_BREAKPOINT) {
			return Math.min(viewportWidth * MOBILE_WIDTH_RATIO, MOBILE_MAX_WIDTH);
		}

		const reservedWidth = QUEUE_RESERVED_REM * getRootFontSizePx() + QUEUE_GAP_PX;
		return Math.max(
			0,
			Math.min(viewportWidth * DESKTOP_WIDTH_RATIO - reservedWidth, DESKTOP_MAX_WIDTH)
		);
	}

	function updatePlayerFrameSize() {
		if (typeof window === 'undefined' || !playerStageEl) return;

		const bounds = playerStageEl.getBoundingClientRect();
		const fitted = fit16x9(bounds.width, bounds.height, getMaxFrameWidth(window.innerWidth));
		frameWidth = fitted.width;
		frameHeight = fitted.height;
	}

	$effect(() => {
		void currentVideoId;
		showDescription = false;
	});

	$effect(() => {
		const stage = playerStageEl;
		void showQueue;
		void showDescription;
		if (typeof window === 'undefined' || !stage) return;

		const rafId = window.requestAnimationFrame(() => {
			updatePlayerFrameSize();
		});

		return () => window.cancelAnimationFrame(rafId);
	});

	$effect(() => {
		const stage = playerStageEl;
		if (!stageResizeObserver || !stage) return;
		stageResizeObserver.observe(stage);
		return () => {
			stageResizeObserver?.unobserve(stage);
		};
	});

	onMount(() => {
		returnUrl = new URLSearchParams(window.location.search).get('return') ?? '/inbox';

		void initializeQueue().then(() => {
			if (!playerState.current.currentVideo && playerState.current.queue.length === 0) {
				goto(resolve(returnUrl as '/inbox'), { replaceState: true });
			}
		});

		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') goto(resolve(returnUrl as '/inbox'));
		};

		const onResize = () => {
			updatePlayerFrameSize();
		};

		stageResizeObserver = new ResizeObserver(() => {
			updatePlayerFrameSize();
		});

		window.addEventListener('keydown', onKey);
		window.addEventListener('resize', onResize);
		void window.requestAnimationFrame(() => {
			updatePlayerFrameSize();
		});

		return () => {
			window.removeEventListener('keydown', onKey);
			window.removeEventListener('resize', onResize);
			stageResizeObserver?.disconnect();
			stageResizeObserver = null;
		};
	});

	function handleBack() {
		goto(resolve(returnUrl as '/inbox'));
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
			{#if playerState.current.currentVideo}
				<WatchLaterButton videoId={playerState.current.currentVideo.id} compact={false} />
			{/if}
			<button
				class="btn btn-ghost btn-sm"
				onclick={() =>
					playerState.current.currentVideo && openSaveVideo(playerState.current.currentVideo)}
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
			<div
				class="player-layout mx-auto flex min-h-0 w-full flex-col gap-4 lg:flex-row lg:items-center lg:justify-center"
			>
				<div
					bind:this={playerStageEl}
					class="player-stage flex h-full min-h-0 flex-1 items-center justify-center"
				>
					<div
						class="player-frame aspect-video w-full"
						style:width={frameWidth > 0 ? `${frameWidth}px` : undefined}
						style:height={frameHeight > 0 ? `${frameHeight}px` : undefined}
					>
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

<style>
	.player-frame {
		max-width: min(90vw, 1600px);
	}

	@media (min-width: 1024px) {
		.player-frame {
			max-width: min(calc(96vw - 24rem - 1rem), 1400px);
		}
	}
</style>
