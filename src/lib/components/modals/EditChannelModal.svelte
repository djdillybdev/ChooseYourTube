<script lang="ts">
	import { api } from '$lib/api';
	import type { ChannelOut, FolderOut } from '$lib/types/api';
	import { invalidate } from '$app/navigation';

	interface Props {
		channel: ChannelOut;
		folders: FolderOut[];
		onClose: () => void;
	}

	let { channel, folders, onClose }: Props = $props();

	let isFavorited = $state(channel.is_favorited);
	let selectedFolder = $state<string | null>(channel.folder_id);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);
	let dialogElement: HTMLDialogElement;

	$effect(() => {
		dialogElement?.showModal();
	});

	/** Flatten the nested folder tree for the <select> */
	function flattenFolders(list: FolderOut[], acc: FolderOut[] = []): FolderOut[] {
		for (const f of list) {
			acc.push(f);
			if (f.children?.length) flattenFolders(f.children, acc);
		}
		return acc;
	}
	let flatFolders = $derived(flattenFolders(folders));

	async function handleSave(e: Event) {
		e.preventDefault();
		isSubmitting = true;
		error = null;
		try {
			await api.channels.update(channel.id, {
				is_favorited: isFavorited,
				folder_id: selectedFolder
			});
			await invalidate('app:channels');
			onClose();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update channel';
		} finally {
			isSubmitting = false;
		}
	}

	async function handleDelete() {
		if (!confirm(`Delete "${channel.title}" and all its videos?`)) return;
		isSubmitting = true;
		error = null;
		try {
			await api.channels.delete(channel.id);
			await invalidate('app:channels');
			await invalidate('app:folders');
			onClose();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to delete channel';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<dialog bind:this={dialogElement} class="modal modal-open">
	<div class="modal-box">
		<!-- Channel identity (read-only header) -->
		<div class="mb-4 flex items-center gap-3">
			{#if channel.thumbnail_url}
				<img src={channel.thumbnail_url} alt={channel.title} class="h-12 w-12 rounded-full object-cover" />
			{:else}
				<div class="flex h-12 w-12 items-center justify-center rounded-full bg-base-300">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="h-6 w-6 text-base-content/40">
						<path stroke-linecap="round" stroke-linejoin="round" d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z" />
					</svg>
				</div>
			{/if}
			<div>
				<h3 class="text-lg font-bold">{channel.title}</h3>
				<p class="text-sm text-base-content/60">@{channel.handle}</p>
			</div>
		</div>

		<form onsubmit={handleSave} class="space-y-4">
			<!-- Favorite toggle -->
			<div class="flex items-center justify-between">
				<span class="label-text">Favorite</span>
				<input type="checkbox" class="toggle toggle-primary" bind:checked={isFavorited} disabled={isSubmitting} />
			</div>

			<!-- Folder select -->
			<div class="form-control">
				<label class="label" for="edit-ch-folder">
					<span class="label-text">Folder</span>
				</label>
				<select id="edit-ch-folder" bind:value={selectedFolder} disabled={isSubmitting} class="select select-bordered w-full">
					<option value={null}>No folder</option>
					{#each flatFolders as f}
						<option value={f.id}>{f.name}</option>
					{/each}
				</select>
			</div>

			<!-- Error -->
			{#if error}
				<div class="alert alert-error">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<span>{error}</span>
				</div>
			{/if}

			<!-- Actions -->
			<div class="modal-action">
				<button type="button" class="btn btn-ghost btn-sm text-error" onclick={handleDelete} disabled={isSubmitting}>
					Delete
				</button>
				<div class="flex-1"></div>
				<button type="button" class="btn btn-ghost" onclick={onClose} disabled={isSubmitting}>Cancel</button>
				<button type="submit" class="btn btn-primary" disabled={isSubmitting}>
					{#if isSubmitting}<span class="loading loading-spinner loading-sm"></span>{/if}
					Save
				</button>
			</div>
		</form>
	</div>
	<form method="dialog" class="modal-backdrop" onclick={onClose}><button>close</button></form>
</dialog>
