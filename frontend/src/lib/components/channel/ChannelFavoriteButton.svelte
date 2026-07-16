<script lang="ts">
	import { invalidate } from '$app/navigation';
	import { api } from '$lib/api';

	interface Props {
		channelId: string;
		channelTitle: string;
		isFavorited: boolean;
	}

	let { channelId, channelTitle, isFavorited }: Props = $props();
	let favorite = $state(false);
	let isUpdating = $state(false);
	let updateError = $state<string | null>(null);

	$effect(() => {
		favorite = isFavorited;
	});

	async function toggleFavorite(event: MouseEvent) {
		event.preventDefault();
		event.stopPropagation();
		if (isUpdating) return;

		const previous = favorite;
		favorite = !previous;
		isUpdating = true;
		updateError = null;
		try {
			const updated = await api.channels.update(channelId, { is_favorited: favorite });
			favorite = updated.is_favorited;
			await invalidate('app:channels');
		} catch (cause) {
			favorite = previous;
			updateError = cause instanceof Error ? cause.message : 'Failed to update favorite';
		} finally {
			isUpdating = false;
		}
	}
</script>

<span class="inline-flex items-center">
	<button
		type="button"
		class="btn btn-square shrink-0 btn-ghost btn-sm"
		class:btn-active={favorite}
		class:text-warning={favorite}
		onclick={toggleFavorite}
		disabled={isUpdating}
		aria-label={favorite
			? `Remove ${channelTitle} from favorites`
			: `Add ${channelTitle} to favorites`}
		title={favorite ? 'Remove from favorites' : 'Add to favorites'}
	>
		{#if isUpdating}
			<span class="loading loading-xs loading-spinner"></span>
		{:else}
			<svg
				viewBox="0 0 24 24"
				fill={favorite ? 'currentColor' : 'none'}
				stroke="currentColor"
				stroke-width="1.5"
				class="h-5 w-5"
				aria-hidden="true"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
				/>
			</svg>
		{/if}
	</button>
	{#if updateError}
		<span class="sr-only" role="alert">{updateError}</span>
	{/if}
</span>
