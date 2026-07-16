<script lang="ts">
	import { invalidate } from '$app/navigation';
	import { api } from '$lib/api';
	import CategoryIconPicker from '$lib/components/ui/CategoryIconPicker.svelte';
	import DialogShell from '$lib/components/ui/DialogShell.svelte';

	interface Props {
		onClose: () => void;
	}

	let { onClose }: Props = $props();
	let name = $state('');
	let iconKey = $state<string | null>(null);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (!name.trim()) return;
		isSubmitting = true;
		error = null;
		try {
			await api.categories.create({ name: name.trim(), icon_key: iconKey });
			await invalidate('app:categories');
			onClose();
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Failed to create category';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<DialogShell
	id="create-category-dialog"
	titleId="create-category-title"
	descriptionId="create-category-description"
	busy={isSubmitting}
	{onClose}
>
	<h2 id="create-category-title" class="text-lg font-bold">Create New Category</h2>
	<p id="create-category-description" class="py-2 text-sm text-base-content/80">
		Categories can contain any number of channels, and channels can appear in several categories.
	</p>
	<form onsubmit={handleSubmit} class="space-y-4">
		<label class="form-control" for="category-name">
			<span class="label-text mb-1">Category Name</span>
			<input
				id="category-name"
				data-dialog-initial-focus
				class="input-bordered input"
				bind:value={name}
				maxlength="255"
				disabled={isSubmitting}
				required
			/>
		</label>
		<CategoryIconPicker
			value={iconKey}
			disabled={isSubmitting}
			onChange={(value) => (iconKey = value)}
		/>
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
</DialogShell>
