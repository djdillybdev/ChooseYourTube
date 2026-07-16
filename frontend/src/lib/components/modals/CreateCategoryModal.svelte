<script lang="ts">
	import { invalidate } from '$app/navigation';
	import { api } from '$lib/api';

	interface Props {
		onClose: () => void;
	}

	let { onClose }: Props = $props();
	let name = $state('');
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);
	let dialogElement: HTMLDialogElement;
	$effect(() => dialogElement?.showModal());

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (!name.trim()) return;
		isSubmitting = true;
		error = null;
		try {
			await api.categories.create({ name: name.trim() });
			await invalidate('app:categories');
			onClose();
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Failed to create category';
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
		<h3 class="text-lg font-bold">Create New Category</h3>
		<p class="py-2 text-sm text-base-content/60">
			Categories can contain any number of channels, and channels can appear in several categories.
		</p>
		<form onsubmit={handleSubmit} class="space-y-4">
			<label class="form-control" for="category-name">
				<span class="label-text mb-1">Category Name</span>
				<input
					id="category-name"
					class="input-bordered input"
					bind:value={name}
					maxlength="255"
					disabled={isSubmitting}
					required
				/>
			</label>
			{#if error}<div class="alert alert-error" role="alert">{error}</div>{/if}
			<div class="modal-action">
				<button type="button" class="btn btn-ghost" onclick={onClose} disabled={isSubmitting}
					>Cancel</button
				>
				<button class="btn btn-primary" type="submit" disabled={isSubmitting || !name.trim()}>
					{isSubmitting ? 'Creating…' : 'Create Category'}
				</button>
			</div>
		</form>
	</div>
	<form method="dialog" class="modal-backdrop">
		<button type="button" onclick={onClose}>close</button>
	</form>
</dialog>
