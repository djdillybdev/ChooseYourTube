<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import { resolve } from '$app/paths';
	import type { PageData } from './$types';
	import { api } from '$lib/api';
	import { playFromPlaylist } from '$lib/stores/playerState.svelte';
	import { formatDuration } from '$lib/utils/formatDuration';
	import { createChannelMap, getChannelTitle } from '$lib/utils/channelLookup';
	import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const channels = $derived(data.channels ?? []);
	const channelMap = $derived(channels.length > 0 ? createChannelMap(channels) : undefined);

	let videos = $state<typeof data.videos>([]);
	let name = $state('');
	let description = $state('');
	let isSavingMeta = $state(false);
	let isDeleting = $state(false);
	let confirmingDelete = $state(false);
	let actionError = $state<string | null>(null);
	let dragIndex = $state<number | null>(null);
	let syncedPlaylistId = $state<string | null>(null);

	$effect(() => {
		if (syncedPlaylistId !== data.playlist.id) {
			videos = [...data.videos];
			name = data.playlist.name;
			description = data.playlist.description ?? '';
			syncedPlaylistId = data.playlist.id;
		}
	});

	async function handlePlay(videoId: string) {
		actionError = null;
		const started = await playFromPlaylist(data.playlist.id, videoId);
		if (!started) {
			actionError = 'Unable to start playback. Please try again.';
			return;
		}
		const returnUrl = window.location.pathname + window.location.search;
		await goto(resolve(`/player?return=${encodeURIComponent(returnUrl)}` as '/player'));
	}

	async function handleSaveMeta(e: Event) {
		e.preventDefault();
		if (!name.trim()) return;
		isSavingMeta = true;
		actionError = null;
		try {
			await api.playlists.update(data.playlist.id, {
				name: name.trim(),
				description: description.trim() || null
			});
			await invalidateAll();
		} catch (err) {
			actionError = err instanceof Error ? err.message : 'Failed to update playlist';
		} finally {
			isSavingMeta = false;
		}
	}

	async function handleDeletePlaylist() {
		isDeleting = true;
		actionError = null;
		try {
			await api.playlists.delete(data.playlist.id);
			confirmingDelete = false;
			await goto(resolve('/playlists'));
		} catch (err) {
			actionError = err instanceof Error ? err.message : 'Failed to delete playlist';
			isDeleting = false;
		}
	}

	async function handleRemoveVideo(videoId: string) {
		actionError = null;
		const previous = videos;
		videos = videos.filter((video) => video.id !== videoId);
		try {
			await api.playlists.removeVideo(data.playlist.id, videoId);
		} catch (err) {
			videos = previous;
			actionError = err instanceof Error ? err.message : 'Failed to remove video';
		}
	}

	function handleDragStart(index: number) {
		dragIndex = index;
	}

	async function handleDrop(index: number) {
		if (dragIndex === null || dragIndex === index) {
			dragIndex = null;
			return;
		}

		const sourceIndex = dragIndex;
		dragIndex = null;
		const dragged = videos[sourceIndex];
		if (!dragged) return;

		const reordered = [...videos];
		reordered.splice(sourceIndex, 1);
		reordered.splice(index, 0, dragged);
		const previous = videos;
		videos = reordered;

		try {
			await api.playlists.moveVideo(data.playlist.id, {
				video_id: dragged.id,
				new_position: index
			});
		} catch (err) {
			videos = previous;
			actionError = err instanceof Error ? err.message : 'Failed to reorder video';
		}
	}
</script>

<svelte:head>
	<title>{data.playlist.name} - Playlists - ChooseYourTube</title>
</svelte:head>

<div class="container mx-auto max-w-7xl p-6">
	<div class="mb-6 flex items-start justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold">{data.playlist.name}</h1>
			<p class="text-sm text-base-content/60">
				{videos.length}
				{videos.length === 1 ? 'video' : 'videos'}
			</p>
		</div>
		<div class="flex items-center gap-2">
			<a href={resolve('/playlists')} class="btn btn-ghost btn-sm">Back</a>
			<button
				class="btn text-error btn-ghost btn-sm"
				onclick={() => (confirmingDelete = true)}
				disabled={isDeleting}
			>
				Delete Playlist
			</button>
		</div>
	</div>

	<form onsubmit={handleSaveMeta} class="mb-6 rounded-box border border-base-300 bg-base-100 p-4">
		<div class="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
			<div>
				<label class="label" for="name">
					<span class="label-text">Name</span>
				</label>
				<input id="name" class="input-bordered input w-full" bind:value={name} required />
			</div>
			<div>
				<label class="label" for="description">
					<span class="label-text">Description</span>
				</label>
				<input id="description" class="input-bordered input w-full" bind:value={description} />
			</div>
			<button class="btn btn-primary" type="submit" disabled={isSavingMeta || !name.trim()}>
				{#if isSavingMeta}<span class="loading loading-sm loading-spinner"></span>{/if}
				Save
			</button>
		</div>
		{#if actionError}
			<p class="mt-2 text-sm text-error">{actionError}</p>
		{/if}
	</form>

	{#if videos.length === 0}
		<div
			class="rounded-box border border-base-300 bg-base-100 p-6 text-center text-base-content/70"
		>
			Playlist is empty. Use Save on any video to add items.
		</div>
	{:else}
		<div class="space-y-2" role="list">
			{#each videos as video, index (video.id)}
				<div
					class="flex items-center gap-3 rounded-box border border-base-300 bg-base-100 p-3"
					class:opacity-60={dragIndex === index}
					role="listitem"
					draggable
					ondragstart={() => handleDragStart(index)}
					ondragover={(e) => e.preventDefault()}
					ondrop={() => void handleDrop(index)}
				>
					<div class="w-6 text-center text-sm text-base-content/60">{index + 1}</div>
					{#if video.thumbnail_url}
						<img
							src={video.thumbnail_url}
							alt={video.title}
							class="h-14 w-24 rounded object-cover"
						/>
					{:else}
						<div
							class="flex h-14 w-24 items-center justify-center rounded bg-base-200 text-xs text-base-content/50"
						>
							No image
						</div>
					{/if}
					<div class="min-w-0 flex-1">
						<p class="line-clamp-2 text-sm font-medium">{video.title}</p>
						<p class="text-xs text-base-content/60">
							{#if channelMap}
								{getChannelTitle(video.channel_id, channelMap)}
							{:else}
								{video.channel_id}
							{/if}
						</p>
					</div>
					{#if video.duration_seconds}
						<span class="text-xs text-base-content/60"
							>{formatDuration(video.duration_seconds)}</span
						>
					{/if}
					<button class="btn btn-ghost btn-sm" onclick={() => void handlePlay(video.id)}
						>Play</button
					>
					<button
						class="btn text-error btn-ghost btn-sm"
						onclick={() => void handleRemoveVideo(video.id)}
					>
						Remove
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>

{#if confirmingDelete}
	<ConfirmDialog
		title="Delete playlist?"
		message={`“${data.playlist.name}” and its ordering will be permanently deleted.`}
		confirmLabel="Delete playlist"
		busy={isDeleting}
		error={actionError}
		onConfirm={handleDeletePlaylist}
		onCancel={() => (confirmingDelete = false)}
	/>
{/if}
