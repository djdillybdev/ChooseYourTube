<script lang="ts">
	import type { ChannelOut } from '$lib/types/api';
	import { page } from '$app/stores';
	import { openEditChannel } from '$lib/stores/modalState.svelte';

	interface Props {
		channel: ChannelOut;
		depth?: number;
	}

	let { channel, depth = 0 }: Props = $props();

	const isActive = $derived($page.params.id === channel.id.toString());

	// Track hover state for this channel
	let isHovered = $state(false);
</script>

<li>
	<div
		class="channel-item flex items-center"
		style="padding-left: {depth * 1}rem"
		onmouseenter={() => (isHovered = true)}
		onmouseleave={() => (isHovered = false)}
	>
		<!-- Spacer to align with folders that have chevrons -->
		<span class="mr-1 w-4"></span>

		<!-- Channel link -->
		<a
			href="/channels/{channel.id}"
			class="flex flex-1 items-center gap-2 rounded px-2 py-1.5 transition-colors hover:bg-base-200"
			class:bg-base-200={isActive}
		>
			<!-- Channel thumbnail or icon -->
			{#if channel.thumbnail_url}
				<img
					src={channel.thumbnail_url}
					alt={channel.title}
					class="h-5 w-5 shrink-0 rounded-full object-cover"
				/>
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
						d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"
					/>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"
					/>
				</svg>
			{/if}

			<span class="text-sm">{channel.title}</span>
		</a>

		<!-- Three-dot menu button (hover-reveal) -->
		{#if isHovered}
			<button
				class="btn btn-square btn-ghost btn-xs"
				onclick={(e) => {
					e.stopPropagation();
					openEditChannel(channel);
				}}
				aria-label="Edit channel"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="h-4 w-4"
				>
					<path
						d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM11.25 18.75a.75.75 0 111.5 0 .75.75 0 01-1.5 0z"
					/>
				</svg>
			</button>
		{/if}
	</div>
</li>

