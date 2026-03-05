<script lang="ts">
	interface Props {
		channelMap?: unknown;
	}

	let { channelMap }: Props = $props();
</script>

<div data-testid="queue-list-stub">QueueList stub {channelMap ? 'with map' : 'without map'}</div>
