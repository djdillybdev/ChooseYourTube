<script lang="ts">
	interface Props {
		channelMap?: unknown;
		variant?: 'panel' | 'page';
		onPlaybackStarted?: () => void | Promise<void>;
	}

	let { channelMap, variant = 'panel', onPlaybackStarted }: Props = $props();
</script>

<div data-testid="queue-list-stub" data-variant={variant}>
	QueueList stub {channelMap ? 'with map' : 'without map'}
	{#if onPlaybackStarted}
		<button type="button" onclick={() => void onPlaybackStarted()}>Play queued video</button>
	{/if}
</div>
