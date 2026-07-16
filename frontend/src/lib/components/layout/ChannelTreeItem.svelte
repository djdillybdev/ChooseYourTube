<script lang="ts">
	import { resolve } from '$app/paths';
	import type { ChannelOut } from '$lib/types/api';
	import { page } from '$app/state';
	import { openEditChannel } from '$lib/stores/modalState.svelte';

	interface Props {
		channel: ChannelOut;
	}

	let { channel }: Props = $props();

	const isActive = $derived(page.params.id === channel.id.toString());
</script>

<li class="group w-full max-w-full min-w-0">
	<div class="channel-item flex w-full max-w-full min-w-0 items-center">
		<!-- Channel link -->
		<a
			href={resolve('/channels/[id]', { id: channel.id })}
			class="flex max-w-full min-w-0 flex-1 items-center gap-2 overflow-hidden rounded px-1 py-1 transition-colors"
			class:bg-base-200={isActive}
			aria-current={isActive ? 'page' : undefined}
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
					class="h-5 w-5 shrink-0"
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

			<span class="min-w-0 truncate text-sm" title={channel.title}>{channel.title}</span>
		</a>
		<button
			class="btn pointer-events-none btn-square shrink-0 opacity-0 btn-ghost transition-opacity btn-xs group-focus-within:pointer-events-auto group-focus-within:opacity-100 group-hover:pointer-events-auto group-hover:opacity-100"
			onclick={() => openEditChannel(channel)}
			aria-label={`Edit ${channel.title}`}
		>
			<svg viewBox="0 0 24 24" fill="currentColor" class="h-4 w-4">
				<path
					d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM11.25 18.75a.75.75 0 111.5 0 .75.75 0 01-1.5 0z"
				/>
			</svg>
		</button>
	</div>
</li>
