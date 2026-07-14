<script lang="ts">
	import { api } from '$lib/api';
	import type { ChannelOut, FolderOut, TagOut } from '$lib/types/api';
	import { invalidate } from '$app/navigation';

	interface Props {
		channel: ChannelOut;
		folders: FolderOut[];
		tags?: TagOut[];
		onClose: () => void;
	}

	let { channel, folders, tags = [], onClose }: Props = $props();

	let isFavorited = $state(false);
	let selectedFolder = $state<string | null>(null);
	let selectedTagIds = $state<string[]>([]);
	let syncedChannelId = $state<string | null>(null);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);
	let dialogElement: HTMLDialogElement;

	$effect(() => {
		if (channel.id !== syncedChannelId) {
			isFavorited = channel.is_favorited;
			selectedFolder = channel.folder_id;
			selectedTagIds = [...channel.tag_ids];
			syncedChannelId = channel.id;
		}
	});

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
				folder_id: selectedFolder,
				tag_ids: selectedTagIds
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

<dialog bind:this={dialogElement} class="modal-open modal">
	<div class="modal-box">
		<!-- Channel identity (read-only header) -->
		<div class="mb-4 flex items-center gap-3">
			{#if channel.thumbnail_url}
				<img
					src={channel.thumbnail_url}
					alt={channel.title}
					class="h-12 w-12 rounded-full object-cover"
				/>
			{:else}
				<div class="flex h-12 w-12 items-center justify-center rounded-full bg-base-300">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						class="h-6 w-6 text-base-content/40"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z"
						/>
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
				<input
					type="checkbox"
					class="toggle toggle-primary"
					bind:checked={isFavorited}
					disabled={isSubmitting}
				/>
			</div>

			<!-- Folder select -->
			<div class="form-control">
				<label class="label" for="edit-ch-folder">
					<span class="label-text">Folder</span>
				</label>
				<select
					id="edit-ch-folder"
					bind:value={selectedFolder}
					disabled={isSubmitting}
					class="select-bordered select w-full"
				>
					<option value={null}>No folder</option>
					{#each flatFolders as f (f.id)}
						<option value={f.id}>{f.name}</option>
					{/each}
				</select>
			</div>

			<div class="form-control">
				<span class="label-text mb-2">Tags</span>
				{#if tags.length === 0}
					<p class="text-sm text-base-content/60">
						Create tags in Settings to categorize channels.
					</p>
				{:else}
					<div class="flex flex-wrap gap-2">
						{#each tags as tag (tag.id)}
							<label class="label cursor-pointer gap-2 rounded border border-base-300 px-2 py-1">
								<input
									type="checkbox"
									class="checkbox checkbox-xs"
									checked={selectedTagIds.includes(tag.id)}
									onchange={(event) => {
										selectedTagIds = event.currentTarget.checked
											? [...new Set([...selectedTagIds, tag.id])]
											: selectedTagIds.filter((id) => id !== tag.id);
									}}
								/>
								<span class="label-text">{tag.name}</span>
							</label>
						{/each}
					</div>
				{/if}
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
	<form method="dialog" class="modal-backdrop">
		<button type="button" onclick={onClose} aria-label="Close modal">close</button>
	</form>
</dialog>
