<script lang="ts">
	import type { ChannelOut } from '$lib/types/api';
	import { api } from '$lib/api';
	import { formatRelativeDate } from '$lib/utils/formatDate';

	interface Props {
		channel: ChannelOut;
	}

	let { channel }: Props = $props();

	let isRefreshing = $state(false);
	let refreshError = $state<string | null>(null);

	async function handleRefresh(e: Event) {
		e.preventDefault();
		e.stopPropagation();

		isRefreshing = true;
		refreshError = null;

		try {
			await api.channels.refresh(channel.id);
			// Success - you might want to invalidate or show a toast here
		} catch (err) {
			refreshError = err instanceof Error ? err.message : 'Failed to refresh channel';
			console.error('Failed to refresh channel:', err);
		} finally {
			isRefreshing = false;
		}
	}
</script>

<a
	href="/channels/{channel.id}"
	class="card card-compact bg-base-100 border border-base-300 shadow-sm transition-all hover:shadow-md hover:border-primary"
>
	<div class="card-body">
		<div class="flex items-start gap-4">
			<!-- Channel Thumbnail/Avatar -->
			{#if channel.thumbnail_url}
				<img
					src={channel.thumbnail_url}
					alt={channel.title}
					class="h-16 w-16 rounded-full object-cover"
				/>
			{:else}
				<div class="flex h-16 w-16 items-center justify-center rounded-full bg-base-300">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="h-8 w-8 text-base-content/40"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z"
						/>
					</svg>
				</div>
			{/if}

			<!-- Channel Info -->
			<div class="flex-1 min-w-0">
				<h3 class="font-semibold text-base truncate">{channel.title}</h3>
				<p class="text-sm text-base-content/60">@{channel.handle}</p>

				<div class="mt-2 flex items-center gap-4 text-xs text-base-content/60">
					{#if channel.total_videos !== undefined}
						<span>{channel.total_videos} videos</span>
					{/if}
					{#if channel.last_updated}
						<span>Updated {formatRelativeDate(channel.last_updated)}</span>
					{/if}
				</div>

				{#if refreshError}
					<div class="mt-2 text-xs text-error">{refreshError}</div>
				{/if}
			</div>

			<!-- Refresh Button -->
			<button
				class="btn btn-ghost btn-sm btn-square shrink-0"
				onclick={handleRefresh}
				disabled={isRefreshing}
				aria-label="Refresh channel"
				title="Refresh channel"
			>
				{#if isRefreshing}
					<span class="loading loading-spinner loading-sm"></span>
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
							d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
						/>
					</svg>
				{/if}
			</button>
		</div>
	</div>
</a>
