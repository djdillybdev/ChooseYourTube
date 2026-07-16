<script lang="ts">
	import { api } from '$lib/api';
	import type { CategoryOut } from '$lib/types/api';
	import { invalidate } from '$app/navigation';
	import { resolve } from '$app/paths';

	interface Props {
		categories: CategoryOut[];
		onClose: () => void;
		onSuccess?: () => void;
	}

	let { categories, onClose, onSuccess }: Props = $props();

	let handle = $state('');
	let selectedCategoryIds = $state<string[]>([]);
	let createdChannelId = $state<string | null>(null);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);

	let dialogElement: HTMLDialogElement;

	// Open the dialog when component mounts
	$effect(() => {
		dialogElement?.showModal();
	});

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!handle.trim()) return;

		isSubmitting = true;
		error = null;

		try {
			const channel = createdChannelId
				? null
				: await api.channels.create({
						handle: handle.trim()
					});
			const channelId = createdChannelId ?? channel?.id;
			if (!channelId) throw new Error('The channel was created without an ID.');
			createdChannelId = channelId;
			if (selectedCategoryIds.length > 0) {
				await api.categories.setForChannel(channelId, { category_ids: selectedCategoryIds });
			}

			await Promise.all([invalidate('app:channels'), invalidate('app:categories')]);

			onSuccess?.();
			onClose();
		} catch (err) {
			error =
				createdChannelId && selectedCategoryIds.length > 0
					? 'The channel was added, but its categories could not be assigned. Retry to finish.'
					: err instanceof Error
						? err.message
						: 'Failed to add channel';
			console.error('Failed to add channel:', err);
		} finally {
			isSubmitting = false;
		}
	}
</script>

<dialog
	bind:this={dialogElement}
	class="modal-open modal"
	oncancel={(event) => {
		event.preventDefault();
		if (!isSubmitting) onClose();
	}}
>
	<div class="modal-box">
		<h3 class="text-lg font-bold">Add YouTube Channel</h3>
		<p class="py-2 text-sm text-base-content/60">
			Enter the channel handle (e.g., @mkbhd) or channel URL
		</p>
		<a class="link text-sm link-primary" href={resolve('/settings/imports')} onclick={onClose}>
			Import subscriptions from YouTube
		</a>

		<form onsubmit={handleSubmit} class="space-y-4">
			<!-- Channel handle input -->
			<div class="form-control">
				<label class="label" for="channel-handle">
					<span class="label-text">Channel Handle or URL</span>
				</label>
				<input
					id="channel-handle"
					type="text"
					placeholder="@channelhandle or youtube.com/..."
					bind:value={handle}
					disabled={isSubmitting}
					class="input-bordered input w-full"
					required
				/>
			</div>

			<fieldset>
				<legend class="label-text mb-2">Categories (optional)</legend>
				{#if categories.length === 0}
					<p class="text-sm text-base-content/60">You can categorize this channel later.</p>
				{:else}
					<div class="flex flex-wrap gap-2">
						{#each categories as category (category.id)}
							<label class="label cursor-pointer gap-2 rounded border border-base-300 px-2 py-1">
								<input
									type="checkbox"
									class="checkbox checkbox-xs"
									checked={selectedCategoryIds.includes(category.id)}
									onchange={(event) => {
										selectedCategoryIds = event.currentTarget.checked
											? [...new Set([...selectedCategoryIds, category.id])]
											: selectedCategoryIds.filter((id) => id !== category.id);
									}}
								/>
								<span>{category.name}</span>
							</label>
						{/each}
					</div>
				{/if}
			</fieldset>

			<!-- Error message -->
			{#if error}
				<div class="alert alert-error">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6 shrink-0 stroke-current"
						fill="none"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<span>{error}</span>
				</div>
			{/if}

			<!-- Actions -->
			<div class="modal-action">
				<button type="button" class="btn btn-ghost" onclick={onClose} disabled={isSubmitting}>
					Cancel
				</button>
				<button type="submit" class="btn btn-primary" disabled={isSubmitting || !handle.trim()}>
					{#if isSubmitting}
						<span class="loading loading-sm loading-spinner"></span>
						Adding...
					{:else}
						{createdChannelId ? 'Retry Category Assignment' : 'Add Channel'}
					{/if}
				</button>
			</div>
		</form>
	</div>
	<form method="dialog" class="modal-backdrop">
		<button type="button" onclick={onClose} aria-label="Close modal">close</button>
	</form>
</dialog>
