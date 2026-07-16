<script lang="ts">
	import { resolve } from '$app/paths';
	import type { ChannelOut } from '$lib/types/api';
	import { api } from '$lib/api';
	import { formatRelativeDate } from '$lib/utils/formatDate';
	import { openEditChannel } from '$lib/stores/modalState.svelte';
	import SyncStatus from './SyncStatus.svelte';
	import { pollSyncRun } from '$lib/utils/syncPolling';
	import { onDestroy } from 'svelte';
	import type { SyncRunOut } from '$lib/types/api';
	import ChannelFavoriteButton from './ChannelFavoriteButton.svelte';

	interface Props {
		channel: ChannelOut;
		backgroundJobsEnabled?: boolean;
	}

	let { channel, backgroundJobsEnabled = true }: Props = $props();

	let isRefreshing = $state(false);
	let refreshError = $state<string | null>(null);
	let activeRun = $state<SyncRunOut | null>(null);
	let cancelled = false;
	onDestroy(() => (cancelled = true));

	async function handleRefresh() {
		isRefreshing = true;
		refreshError = null;

		try {
			const run = await api.channels.refresh(channel.id);
			activeRun = run;
			const completed = await pollSyncRun(
				run.id,
				(id) => api.syncRuns.get(id),
				(updated) => (activeRun = updated),
				() => cancelled
			);
			if (completed?.status === 'failed') refreshError = completed.error_message;
		} catch (err) {
			refreshError = err instanceof Error ? err.message : 'Failed to refresh channel';
			console.error('Failed to refresh channel:', err);
		} finally {
			isRefreshing = false;
		}
	}
</script>

<article
	class="card-compact card border border-base-300 bg-base-100 shadow-sm transition-all hover:border-primary hover:shadow-md"
>
	<div class="card-body">
		<div class="flex items-start gap-4">
			<a
				href={resolve('/channels/[id]', { id: channel.id })}
				class="flex min-w-0 flex-1 items-start gap-4 rounded focus-visible:outline-offset-4"
			>
				<!-- Channel Thumbnail/Avatar -->
				{#if channel.thumbnail_url}
					<img
						src={channel.thumbnail_url}
						alt=""
						class="h-16 w-16 shrink-0 rounded-full object-cover"
					/>
				{:else}
					<div class="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-base-300">
						<svg
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							class="h-8 w-8 text-base-content/60"
							aria-hidden="true"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="1.5"
								d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z"
							/>
						</svg>
					</div>
				{/if}

				<div class="min-w-0 flex-1">
					<h3 class="truncate text-base font-semibold">{channel.title}</h3>
					<p class="text-sm text-base-content/80">@{channel.handle}</p>

					<div
						class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-base-content/80"
					>
						{#if channel.total_videos !== undefined}
							<span>{channel.total_videos} videos</span>
						{/if}
						{#if channel.last_updated}
							<span>Updated {formatRelativeDate(channel.last_updated)}</span>
						{/if}
					</div>
					<SyncStatus sync={activeRun ?? channel.latest_sync} compact />
				</div>
			</a>

			<div class="flex shrink-0 flex-wrap items-center justify-end gap-1">
				<ChannelFavoriteButton
					channelId={channel.id}
					channelTitle={channel.title}
					isFavorited={channel.is_favorited}
				/>

				<button
					class="btn btn-square btn-ghost btn-sm"
					onclick={() => openEditChannel(channel)}
					aria-label={`Edit ${channel.title}`}
					title="Edit channel"
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
							d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z"
						/>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
						/>
					</svg>
				</button>

				<button
					class="btn btn-square btn-ghost btn-sm"
					onclick={() => void handleRefresh()}
					disabled={isRefreshing || !backgroundJobsEnabled}
					aria-label={`Refresh ${channel.title}`}
					title={backgroundJobsEnabled ? 'Refresh channel' : 'Live refresh is disabled in the demo'}
				>
					{#if isRefreshing}
						<span class="loading loading-sm loading-spinner"></span>
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

		{#if refreshError}<p class="mt-2 text-xs text-error" role="alert">{refreshError}</p>{/if}
		<div class="sr-only" aria-live="polite">
			{activeRun ? `Refresh ${activeRun.status}` : ''}
		</div>
	</div>
</article>
