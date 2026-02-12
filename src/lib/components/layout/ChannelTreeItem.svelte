<script lang="ts">
	import type { ChannelOut } from '$lib/types/api';
	import { page } from '$app/stores';

	interface Props {
		channel: ChannelOut;
		depth?: number;
	}

	let { channel, depth = 0 }: Props = $props();

	const isActive = $derived($page.params.id === channel.id.toString());
</script>

<li>
	<div
		class="channel-item flex items-center"
		style="padding-left: {depth * 1}rem"
	>
		<!-- Spacer to align with folders that have chevrons -->
		<span class="mr-1 w-4"></span>

		<!-- Channel link -->
		<a
			href="/channels/{channel.id}"
			class="flex flex-1 items-center gap-2 rounded px-2 py-1.5 transition-colors"
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
	</div>
</li>

