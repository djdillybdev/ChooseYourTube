<script lang="ts">
	import { api } from '$lib/api';
	import type { FolderOut } from '$lib/types/api';
	import { invalidate } from '$app/navigation';

	interface Props {
		folders: FolderOut[];
		onClose: () => void;
		onSuccess?: () => void;
	}

	let { folders, onClose, onSuccess }: Props = $props();

	let name = $state('');
	let selectedParentId = $state<string | undefined>(undefined);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);

	let dialogElement: HTMLDialogElement;

	// Open the dialog when component mounts
	$effect(() => {
		dialogElement?.showModal();
	});

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!name.trim()) return;

		isSubmitting = true;
		error = null;

		try {
			await api.folders.create({
				name: name.trim(),
				parent_id: selectedParentId
			});

			// Invalidate to refresh folders list
			await invalidate('app:folders');

			onSuccess?.();
			onClose();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create folder';
			console.error('Failed to create folder:', err);
		} finally {
			isSubmitting = false;
		}
	}
</script>

<dialog bind:this={dialogElement} class="modal modal-open">
	<div class="modal-box">
		<h3 class="text-lg font-bold">Create New Folder</h3>
		<p class="py-2 text-sm text-base-content/60">
			Organize your channels into folders for easy navigation
		</p>

		<form onsubmit={handleSubmit} class="space-y-4">
			<!-- Folder name input -->
			<div class="form-control">
				<label class="label" for="folder-name">
					<span class="label-text">Folder Name</span>
				</label>
				<input
					id="folder-name"
					type="text"
					placeholder="My Folder"
					bind:value={name}
					disabled={isSubmitting}
					class="input input-bordered w-full"
					required
				/>
			</div>

			<!-- Parent folder selection (optional) -->
			<div class="form-control">
				<label class="label" for="parent-folder-select">
					<span class="label-text">Parent Folder (optional)</span>
				</label>
				<select
					id="parent-folder-select"
					bind:value={selectedParentId}
					disabled={isSubmitting}
					class="select select-bordered w-full"
				>
					<option value={undefined}>No parent (top level)</option>
					{#each folders as folder}
						<option value={folder.id}>{folder.name}</option>
					{/each}
				</select>
			</div>

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
				<button type="submit" class="btn btn-primary" disabled={isSubmitting || !name.trim()}>
					{#if isSubmitting}
						<span class="loading loading-spinner loading-sm"></span>
						Creating...
					{:else}
						Create Folder
					{/if}
				</button>
			</div>
		</form>
	</div>
	<form method="dialog" class="modal-backdrop" onclick={onClose}>
		<button>close</button>
	</form>
</dialog>
