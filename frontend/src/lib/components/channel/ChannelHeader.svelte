<script lang="ts">
	import type { ChannelOut, LatestSyncSummary, SyncRunOut } from '$lib/types/api';
	import ChannelFavoriteButton from './ChannelFavoriteButton.svelte';
	import SyncStatus from './SyncStatus.svelte';

	interface Props {
		channel: ChannelOut;
		countLabel: string;
		updatedLabel?: string;
		sync?: LatestSyncSummary | SyncRunOut | null;
		syncAnnouncement?: string;
		refreshError?: string | null;
		isRefreshing?: boolean;
		canRefresh?: boolean;
		refreshDisabledReason?: string;
		refreshLabel?: string;
		showFavorite?: boolean;
		onEdit: () => void;
		onRefresh: () => void | Promise<void>;
	}

	let {
		channel,
		countLabel,
		updatedLabel,
		sync,
		syncAnnouncement = '',
		refreshError = null,
		isRefreshing = false,
		canRefresh = true,
		refreshDisabledReason,
		refreshLabel = 'Refresh',
		showFavorite = false,
		onEdit,
		onRefresh
	}: Props = $props();
</script>

<header
	class="mb-6 grid min-w-0 grid-cols-[4rem_minmax(0,1fr)] items-start gap-3 sm:grid-cols-[6rem_minmax(0,1fr)_auto] sm:gap-5"
>
	{#if channel.thumbnail_url}
		<img
			src={channel.thumbnail_url}
			alt=""
			class="h-16 w-16 rounded-full object-cover sm:h-24 sm:w-24"
		/>
	{:else}
		<div
			class="flex h-16 w-16 items-center justify-center rounded-full bg-base-300 sm:h-24 sm:w-24"
			aria-hidden="true"
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-8 w-8 sm:h-12 sm:w-12">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="1.5"
					d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z"
				/>
			</svg>
		</div>
	{/if}

	<div class="min-w-0">
		<h1 class="text-2xl leading-tight font-bold break-words sm:text-3xl">{channel.title}</h1>
		{#if channel.handle}<p class="mt-1 break-all text-base-content">@{channel.handle}</p>{/if}
		<div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-base-content">
			<span>{countLabel}</span>
			{#if updatedLabel}<span>{updatedLabel}</span>{/if}
		</div>
		{#if refreshError}<p class="mt-2 text-sm text-error" role="alert">{refreshError}</p>{/if}
		<div class="mt-2"><SyncStatus {sync} /></div>
		<div class="sr-only" aria-live="polite">{syncAnnouncement}</div>
	</div>

	<div class="col-span-2 flex flex-wrap items-center gap-2 sm:col-span-1 sm:justify-end">
		{#if showFavorite}
			<ChannelFavoriteButton
				channelId={channel.id}
				channelTitle={channel.title}
				isFavorited={channel.is_favorited}
			/>
		{/if}
		<button class="btn btn-ghost btn-sm" type="button" onclick={onEdit} aria-label="Edit channel">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5" aria-hidden="true">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="1.5"
					d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931"
				/>
			</svg>
			<span class="sm:hidden">Edit</span>
		</button>
		<button
			class="btn gap-2 btn-primary"
			type="button"
			onclick={() => void onRefresh()}
			disabled={isRefreshing || !canRefresh}
			title={!canRefresh ? refreshDisabledReason : refreshLabel}
		>
			{#if isRefreshing}<span class="loading loading-sm loading-spinner" aria-hidden="true"
				></span>{/if}
			{isRefreshing ? 'Refreshing…' : refreshLabel}
		</button>
	</div>
</header>
