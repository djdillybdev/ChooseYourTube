<script lang="ts">
	import { api } from '$lib/api';
	import type { FolderOut } from '$lib/types/api';
	import { invalidate } from '$app/navigation';
	import { resolve } from '$app/paths';

	interface Props {
		folders: FolderOut[];
		onClose: () => void;
		onSuccess?: () => void;
	}

	let { folders, onClose, onSuccess }: Props = $props();

	let handle = $state('');
	let selectedFolderId = $state<string | undefined>(undefined);
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
			await api.channels.create({
				handle: handle.trim(),
				folder_id: selectedFolderId
			});

			// Invalidate to refresh channels list
			await invalidate('app:channels');

			onSuccess?.();
			onClose();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to add channel';
			console.error('Failed to add channel:', err);
		} finally {
			isSubmitting = false;
		}
	}
</script>

<dialog bind:this={dialogElement} class="modal-open modal">
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

			<!-- Folder selection (optional) -->
			<div class="form-control">
				<label class="label" for="folder-select">
					<span class="label-text">Folder (optional)</span>
				</label>
				<select
					id="folder-select"
					bind:value={selectedFolderId}
					disabled={isSubmitting}
					class="select-bordered select w-full"
				>
					<option value={undefined}>No folder</option>
					{#each folders as folder (folder.id)}
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
				<button type="submit" class="btn btn-primary" disabled={isSubmitting || !handle.trim()}>
					{#if isSubmitting}
						<span class="loading loading-sm loading-spinner"></span>
						Adding...
					{:else}
						Add Channel
					{/if}
				</button>
			</div>
		</form>
	</div>
	<form method="dialog" class="modal-backdrop">
		<button type="button" onclick={onClose} aria-label="Close modal">close</button>
	</form>
</dialog>
