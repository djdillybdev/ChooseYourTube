<script lang="ts">
	import type { VideoOut, ChannelOut } from '$lib/types/api';
	import VideoCard from './VideoCard.svelte';
	import EmptyState from '../ui/EmptyState.svelte';

	interface Props {
		videos: VideoOut[];
		channelMap?: Map<string, ChannelOut>;
	}

	let { videos, channelMap }: Props = $props();

	/** Optimistic update for watched / favorite toggles */
	function handleVideoUpdate(updated: VideoOut) {
		videos = videos.map((v) => (v.id === updated.id ? updated : v));
	}
</script>

<div class="video-list space-y-3">
	{#each videos as video (video.id)}
		<VideoCard {video} {channelMap} onUpdate={handleVideoUpdate} />
	{/each}

	{#if videos.length === 0}
		<EmptyState
			title="No videos found"
			message="Try adjusting your filters or add some channels to get started."
			icon="video"
		/>
	{/if}
</div>
