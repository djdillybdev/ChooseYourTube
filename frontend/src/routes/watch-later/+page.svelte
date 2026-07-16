<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { api } from '$lib/api';
	import { playFromPlaylist } from '$lib/stores/playerState.svelte';
	import { useWatchLater } from '$lib/stores/watchLater.svelte';
	import { createChannelMap, getChannelTitle } from '$lib/utils/channelLookup';
	import { formatDuration } from '$lib/utils/formatDuration';
	import type { PageData } from './$types';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();
	const watchLater = useWatchLater();
	const channelMap = $derived(createChannelMap(data.channels ?? []));
	let videos = $state<typeof data.videos>([]);
	let dragIndex = $state<number | null>(null);
	let error = $state<string | null>(null);
	let announcement = $state('');

	$effect(() => {
		const byId = new Map(data.videos.map((video) => [video.id, video]));
		videos = (watchLater.playlist?.video_ids ?? [])
			.map((id) => byId.get(id))
			.filter((video): video is (typeof data.videos)[number] => Boolean(video));
	});

	async function play(videoId: string) {
		if (!(await playFromPlaylist(data.playlist.id, videoId))) {
			error = 'Unable to start playback.';
			return;
		}
		await goto(resolve(`/player?return=${encodeURIComponent('/watch-later')}` as '/player'));
	}

	async function remove(videoId: string) {
		const previous = videos;
		videos = videos.filter((video) => video.id !== videoId);
		error = null;
		try {
			await watchLater.setSaved(videoId, false);
		} catch (cause) {
			videos = previous;
			error = cause instanceof Error ? cause.message : 'Could not remove the video.';
		}
	}

	async function reorder(source: number, index: number) {
		if (source === index || source < 0 || index < 0 || index >= videos.length) return;
		const moved = videos[source];
		if (!moved) return;
		const previous = videos;
		const reordered = [...videos];
		reordered.splice(source, 1);
		reordered.splice(index, 0, moved);
		videos = reordered;
		try {
			const updated = await api.playlists.moveVideo(data.playlist.id, {
				video_id: moved.id,
				new_position: index
			});
			watchLater.sync(updated);
			announcement = `Moved ${moved.title} to position ${index + 1} of ${videos.length}.`;
		} catch (cause) {
			videos = previous;
			error = cause instanceof Error ? cause.message : 'Could not reorder Watch Later.';
		}
	}

	async function drop(index: number) {
		if (dragIndex === null) return;
		const source = dragIndex;
		dragIndex = null;
		await reorder(source, index);
	}
</script>

<svelte:head><title>Watch Later - ChooseYourTube</title></svelte:head>

<div class="container mx-auto max-w-7xl px-4 py-6 sm:px-6">
	<PageHeader
		title="Watch Later"
		description={`${videos.length} saved ${videos.length === 1 ? 'video' : 'videos'}`}
	/>
	{#if error}<div class="mb-4 alert alert-error" role="alert">{error}</div>{/if}
	<p class="sr-only" aria-live="polite">{announcement}</p>
	{#if videos.length === 0}
		<div class="rounded-box border border-base-300 bg-base-100 p-10 text-center">
			<h2 class="text-lg font-semibold">Nothing saved yet</h2>
			<p class="mt-1 text-base-content">
				Use the bookmark button on any video card or in the player to save it here.
			</p>
			<a href={resolve('/inbox')} class="btn mt-4 btn-sm btn-primary">Browse Inbox</a>
		</div>
	{:else}
		<div class="space-y-2" role="list">
			{#each videos as video, index (video.id)}
				<div
					class="flex items-center gap-3 rounded-box border border-base-300 bg-base-100 p-3"
					role="listitem"
					draggable
					ondragstart={() => (dragIndex = index)}
					ondragover={(event) => event.preventDefault()}
					ondrop={() => void drop(index)}
				>
					<span class="w-6 text-center text-sm text-base-content/50">{index + 1}</span>
					{#if video.thumbnail_url}<img
							src={video.thumbnail_url}
							alt=""
							class="h-14 w-24 rounded object-cover"
						/>{/if}
					<div class="min-w-0 flex-1">
						<p class="line-clamp-2 text-sm font-medium">{video.title}</p>
						<p class="text-xs text-base-content">
							{getChannelTitle(video.channel_id, channelMap)}
						</p>
					</div>
					{#if video.duration_seconds}<span class="text-xs text-base-content"
							>{formatDuration(video.duration_seconds)}</span
						>{/if}
					<button class="btn btn-ghost btn-sm" onclick={() => void play(video.id)}>Play</button>
					<div class="join" aria-label={`Reorder ${video.title}`}>
						<button
							type="button"
							class="btn join-item btn-square btn-ghost btn-sm"
							onclick={() => void reorder(index, index - 1)}
							disabled={index === 0}
							aria-label={`Move ${video.title} up`}>↑</button
						>
						<button
							type="button"
							class="btn join-item btn-square btn-ghost btn-sm"
							onclick={() => void reorder(index, index + 1)}
							disabled={index === videos.length - 1}
							aria-label={`Move ${video.title} down`}>↓</button
						>
					</div>
					<button class="btn text-error btn-ghost btn-sm" onclick={() => void remove(video.id)}
						>Remove</button
					>
				</div>
			{/each}
		</div>
	{/if}
</div>
