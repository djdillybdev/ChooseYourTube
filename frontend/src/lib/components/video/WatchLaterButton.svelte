<script lang="ts">
	import { useWatchLater } from '$lib/stores/watchLater.svelte';
	import { actionStatus } from '$lib/stores/actionStatus.svelte';

	interface Props {
		videoId: string;
		compact?: boolean;
	}

	let { videoId, compact = true }: Props = $props();
	const watchLater = useWatchLater();
	let error = $state<string | null>(null);
	let saved = $derived(watchLater.isSaved(videoId));
	let pending = $derived(watchLater.isPending(videoId));

	async function toggle(event: MouseEvent) {
		event.stopPropagation();
		error = null;
		const willSave = !saved;
		try {
			await watchLater.toggle(videoId);
			actionStatus.announce(willSave ? 'Saved to Watch Later.' : 'Removed from Watch Later.');
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Could not update Watch Later.';
		}
	}
</script>

<div class="relative inline-flex items-center gap-1">
	<button
		type="button"
		class:btn-square={compact}
		class="btn btn-ghost btn-sm"
		class:btn-active={saved}
		class:text-primary={saved}
		disabled={pending}
		onclick={toggle}
		aria-pressed={saved}
		aria-label={saved ? 'Remove from Watch Later' : 'Save to Watch Later'}
		title={saved ? 'Remove from Watch Later' : 'Save to Watch Later'}
	>
		{#if pending}
			<span class="loading loading-xs loading-spinner"></span>
		{:else}
			<svg
				viewBox="0 0 24 24"
				fill={saved ? 'currentColor' : 'none'}
				stroke="currentColor"
				class="h-5 w-5"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="1.5"
					d="M17.25 6.75v12L12 15.75 6.75 18.75v-12A2.25 2.25 0 019 4.5h6a2.25 2.25 0 012.25 2.25z"
				/>
			</svg>
			{#if !compact}<span>{saved ? 'Saved' : 'Watch Later'}</span>{/if}
		{/if}
	</button>
	{#if error}<span class="max-w-48 text-xs text-error" role="alert">{error}</span>{/if}
	<span class="sr-only" aria-live="polite">{pending ? 'Updating Watch Later' : ''}</span>
</div>
