<script lang="ts">
	import { goto, invalidate } from '$app/navigation';
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { api } from '$lib/api';
	import type { CategoryOut, ChannelOut } from '$lib/types/api';
	import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte';
	import CategoryIconPicker from '$lib/components/ui/CategoryIconPicker.svelte';
	import DialogShell from '$lib/components/ui/DialogShell.svelte';

	interface Props {
		category: CategoryOut;
		channels: ChannelOut[];
		onClose: () => void;
	}

	let { category, channels, onClose }: Props = $props();
	let name = $state('');
	let iconKey = $state<string | null>(null);
	let selectedChannelIds = $state<string[]>([]);
	let syncedCategoryId = $state<string | null>(null);
	let isSubmitting = $state(false);
	let confirmingDelete = $state(false);
	let error = $state<string | null>(null);

	$effect(() => {
		if (category.id !== syncedCategoryId) {
			name = category.name;
			iconKey = category.icon_key ?? null;
			selectedChannelIds = [...(category.channel_ids ?? [])];
			syncedCategoryId = category.id;
		}
	});

	function toggleChannel(id: string, selected: boolean) {
		selectedChannelIds = selected
			? [...new Set([...selectedChannelIds, id])]
			: selectedChannelIds.filter((channelId) => channelId !== id);
	}

	async function handleSave(event: SubmitEvent) {
		event.preventDefault();
		isSubmitting = true;
		error = null;
		try {
			await api.categories.update(category.id, {
				name: name.trim(),
				icon_key: iconKey
			});
			await api.categories.setChannels(category.id, { channel_ids: selectedChannelIds });
			await Promise.all([invalidate('app:categories'), invalidate('app:channels')]);
			onClose();
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Failed to update category';
		} finally {
			isSubmitting = false;
		}
	}

	async function handleDelete() {
		isSubmitting = true;
		error = null;
		try {
			const deletingCurrentCategory = page.url.pathname === `/categories/${category.id}`;
			await api.categories.delete(category.id);
			onClose();
			if (deletingCurrentCategory) await goto(resolve('/inbox'));
			await invalidate('app:categories');
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Failed to delete category';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<DialogShell id="edit-category-dialog" titleId="edit-category-title" busy={isSubmitting} {onClose}>
	<h2 id="edit-category-title" class="text-lg font-bold">Edit Category</h2>
	<form onsubmit={handleSave} class="mt-4 space-y-4">
		<label class="form-control" for="edit-category-name">
			<span class="label-text mb-1">Category Name</span>
			<input
				id="edit-category-name"
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

		<fieldset>
			<legend class="label-text mb-2">Channels</legend>
			{#if channels.length === 0}
				<p class="text-sm text-base-content/60">Add a channel before assigning it here.</p>
			{:else}
				<div class="max-h-64 space-y-1 overflow-y-auto rounded border border-base-300 p-2">
					{#each [...channels].sort( (a, b) => a.title.localeCompare(b.title) ) as channel (channel.id)}
						<label
							class="label cursor-pointer justify-start gap-3 rounded px-2 py-1 hover:bg-base-200"
						>
							<input
								type="checkbox"
								class="checkbox checkbox-sm"
								checked={selectedChannelIds.includes(channel.id)}
								onchange={(event) => toggleChannel(channel.id, event.currentTarget.checked)}
							/>
							<span>{channel.title}</span>
						</label>
					{/each}
				</div>
			{/if}
		</fieldset>

		{#if error}<div class="alert alert-error" role="alert">{error}</div>{/if}
		<div class="modal-action">
			<button
				type="button"
				class="btn text-error btn-ghost btn-sm"
				onclick={() => (confirmingDelete = true)}
				disabled={isSubmitting}>Delete</button
			>
			<div class="flex-1"></div>
			<button type="button" class="btn btn-ghost" onclick={onClose} disabled={isSubmitting}
				>Cancel</button
			>
			<button type="submit" class="btn btn-primary" disabled={isSubmitting || !name.trim()}>
				{isSubmitting ? 'Saving…' : 'Save'}
			</button>
		</div>
	</form>
</DialogShell>

{#if confirmingDelete}
	<ConfirmDialog
		title="Delete category?"
		message={`“${category.name}” will be deleted. Its channels will remain in your library.`}
		confirmLabel="Delete category"
		busy={isSubmitting}
		{error}
		onConfirm={handleDelete}
		onCancel={() => (confirmingDelete = false)}
	/>
{/if}
