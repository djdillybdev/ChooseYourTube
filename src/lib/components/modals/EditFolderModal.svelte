<script lang="ts">
	import { api } from '$lib/api';
	import type { FolderOut } from '$lib/types/api';
	import { invalidate } from '$app/navigation';

	interface Props {
		folder: FolderOut;
		folders: FolderOut[];
		onClose: () => void;
	}

	let { folder, folders, onClose }: Props = $props();

	let name = $state(folder.name);
	let selectedParentId = $state<string | null>(folder.parent_id);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);
	let dialogElement: HTMLDialogElement;

	$effect(() => {
		dialogElement?.showModal();
	});

	/**
	 * Collect IDs of every descendant of `targetId` in the folder tree.
	 * Used to filter the parent-folder <select> and prevent cycles.
	 */
	function getDescendantIds(targetId: string, list: FolderOut[]): Set<string> {
		const ids = new Set<string>();
		function collectChildren(items: FolderOut[]) {
			for (const f of items) {
				ids.add(f.id);
				if (f.children?.length) collectChildren(f.children);
			}
		}
		function find(items: FolderOut[]) {
			for (const f of items) {
				if (f.id === targetId) {
					collectChildren(f.children ?? []);
					return;
				}
				find(f.children ?? []);
			}
		}
		find(list);
		return ids;
	}

	/** Flatten tree, excluding self + descendants */
	let parentOptions = $derived(() => {
		const excluded = getDescendantIds(folder.id, folders);
		excluded.add(folder.id);
		const result: FolderOut[] = [];
		(function flatten(items: FolderOut[]) {
			for (const f of items) {
				if (!excluded.has(f.id)) result.push(f);
				flatten(f.children ?? []);
			}
		})(folders);
		return result;
	});

	async function handleSave(e: Event) {
		e.preventDefault();
		if (!name.trim()) return;
		isSubmitting = true;
		error = null;
		try {
			await api.folders.update(folder.id, {
				name: name.trim(),
				parent_id: selectedParentId
			});
			await invalidate('app:folders');
			onClose();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update folder';
		} finally {
			isSubmitting = false;
		}
	}

	async function handleDelete() {
		if (!confirm(`Delete folder "${folder.name}"? Channels inside will move to root.`)) return;
		isSubmitting = true;
		error = null;
		try {
			await api.folders.delete(folder.id);
			await invalidate('app:folders');
			await invalidate('app:channels');
			onClose();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to delete folder';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<dialog bind:this={dialogElement} class="modal-open modal">
	<div class="modal-box">
		<div class="mb-4 flex items-center gap-3">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
				class="h-8 w-8 text-primary"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
				/>
			</svg>
			<h3 class="text-lg font-bold">Edit Folder</h3>
		</div>

		<form onsubmit={handleSave} class="space-y-4">
			<div class="form-control">
				<label class="label" for="edit-folder-name">
					<span class="label-text">Name</span>
				</label>
				<input
					id="edit-folder-name"
					type="text"
					bind:value={name}
					disabled={isSubmitting}
					class="input-bordered input w-full"
					required
				/>
			</div>

			<div class="form-control">
				<label class="label" for="edit-folder-parent">
					<span class="label-text">Parent Folder</span>
				</label>
				<select
					id="edit-folder-parent"
					bind:value={selectedParentId}
					disabled={isSubmitting}
					class="select-bordered select w-full"
				>
					<option value={null}>Top level (no parent)</option>
					{#each parentOptions() as f}
						<option value={f.id}>{f.name}</option>
					{/each}
				</select>
			</div>

			<!-- Error -->
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
				<button
					type="button"
					class="btn text-error btn-ghost btn-sm"
					onclick={handleDelete}
					disabled={isSubmitting}
				>
					Delete
				</button>
				<div class="flex-1"></div>
				<button type="button" class="btn btn-ghost" onclick={onClose} disabled={isSubmitting}
					>Cancel</button
				>
				<button type="submit" class="btn btn-primary" disabled={isSubmitting}>
					{#if isSubmitting}<span class="loading loading-sm loading-spinner"></span>{/if}
					Save
				</button>
			</div>
		</form>
	</div>
	<form method="dialog" class="modal-backdrop" onclick={onClose}><button>close</button></form>
</dialog>
