<script lang="ts">
	import { api } from '$lib/api';
	import type { PlaylistOut, TagOut, VideoOut } from '$lib/types/api';
	import { isManualPlaylist } from '$lib/utils/playlistScope';
	import { useWatchLater } from '$lib/stores/watchLater.svelte';

	interface Props {
		video: VideoOut;
		tags?: TagOut[];
		onClose: () => void;
	}

	let { video, tags = [], onClose }: Props = $props();
	const watchLater = useWatchLater();

	let dialogElement: HTMLDialogElement;
	let playlists = $state<PlaylistOut[]>([]);
	let initialMemberIds = $state<string[]>([]);
	let selectedIds = $state<string[]>([]);
	let isLoading = $state(true);
	let isSaving = $state(false);
	let isCreating = $state(false);
	let error = $state<string | null>(null);
	let newName = $state('');
	let newDescription = $state('');
	let saveToWatchLater = $state(false);
	let selectedTagIds = $state<string[]>([]);
	let syncedVideoId = $state<string | null>(null);

	$effect(() => {
		if (syncedVideoId !== video.id) {
			saveToWatchLater = watchLater.isSaved(video.id);
			selectedTagIds = [...video.tag_ids];
			syncedVideoId = video.id;
		}
	});

	$effect(() => {
		dialogElement?.showModal();
		void loadPlaylists();
	});

	async function loadPlaylists() {
		isLoading = true;
		error = null;
		try {
			const all: PlaylistOut[] = [];
			let response = await api.playlists.list({ is_system: false, limit: 200, offset: 0 });
			do {
				all.push(...response.items);
				if (!response.has_more) break;
				response = await api.playlists.list({
					is_system: false,
					limit: response.limit,
					offset: response.offset + response.limit
				});
			} while (response.has_more);

			const manualPlaylists = all.filter(isManualPlaylist);
			const membershipResults = await Promise.allSettled(
				manualPlaylists.map(async (playlist) => {
					const detail = await api.playlists.get(playlist.id);
					return detail.video_ids.includes(video.id) ? playlist.id : null;
				})
			);
			const memberIds = membershipResults
				.filter(
					(result): result is PromiseFulfilledResult<string | null> => result.status === 'fulfilled'
				)
				.map((result) => result.value)
				.filter((playlistId): playlistId is string => Boolean(playlistId));

			playlists = manualPlaylists;
			initialMemberIds = memberIds;
			selectedIds = [...memberIds];
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load playlists';
		} finally {
			isLoading = false;
		}
	}

	function toggleSelection(playlistId: string, checked: boolean) {
		if (checked) {
			selectedIds = [...new Set([...selectedIds, playlistId])];
			return;
		}
		selectedIds = selectedIds.filter((id) => id !== playlistId);
	}

	function toggleTag(tagId: string, checked: boolean) {
		selectedTagIds = checked
			? [...new Set([...selectedTagIds, tagId])]
			: selectedTagIds.filter((id) => id !== tagId);
	}

	async function handleCreatePlaylist(e: Event) {
		e.preventDefault();
		if (!newName.trim()) return;

		isCreating = true;
		error = null;
		try {
			const created = await api.playlists.create({
				name: newName.trim(),
				description: newDescription.trim() || undefined
			});
			playlists = [...playlists, created];
			selectedIds = [...new Set([...selectedIds, created.id])];
			newName = '';
			newDescription = '';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create playlist';
		} finally {
			isCreating = false;
		}
	}

	async function handleSave() {
		const initialSet = new Set(initialMemberIds);
		const selectedSet = new Set(selectedIds);
		const toAdd = selectedIds.filter((playlistId) => !initialSet.has(playlistId));
		const toRemove = initialMemberIds.filter((playlistId) => !selectedSet.has(playlistId));

		const watchLaterChanged = saveToWatchLater !== watchLater.isSaved(video.id);
		const tagsChanged =
			selectedTagIds.length !== video.tag_ids.length ||
			selectedTagIds.some((id) => !video.tag_ids.includes(id));

		if (toAdd.length === 0 && toRemove.length === 0 && !watchLaterChanged && !tagsChanged) {
			onClose();
			return;
		}

		isSaving = true;
		error = null;
		try {
			await Promise.all([
				...toAdd.map((playlistId) =>
					api.playlists.addVideo(playlistId, {
						video_id: video.id
					})
				),
				...toRemove.map((playlistId) => api.playlists.removeVideo(playlistId, video.id)),
				...(watchLaterChanged ? [watchLater.setSaved(video.id, saveToWatchLater)] : []),
				...(tagsChanged ? [api.videos.update(video.id, { tag_ids: selectedTagIds })] : [])
			]);
			onClose();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to save video';
		} finally {
			isSaving = false;
		}
	}
</script>

<dialog bind:this={dialogElement} class="modal-open modal">
	<div class="modal-box max-w-2xl">
		<h3 class="text-lg font-bold">Save Video to Playlists</h3>
		<p class="mt-1 line-clamp-2 text-sm text-base-content/70">{video.title}</p>

		<label
			class="mt-4 flex cursor-pointer items-center gap-3 rounded-box border border-primary/30 bg-primary/5 p-3"
		>
			<input type="checkbox" class="checkbox checkbox-primary" bind:checked={saveToWatchLater} />
			<div>
				<p class="font-semibold">Watch Later</p>
				<p class="text-xs text-base-content/60">Keep this video in your quick-access list.</p>
			</div>
		</label>

		<h4 class="mt-4 text-sm font-semibold">Custom playlists</h4>
		<div class="my-4 max-h-72 overflow-y-auto rounded-box border border-base-300 p-2">
			{#if isLoading}
				<div class="flex items-center gap-2 p-2 text-sm text-base-content/70">
					<span class="loading loading-sm loading-spinner"></span>
					Loading playlists...
				</div>
			{:else if playlists.length === 0}
				<p class="p-2 text-sm text-base-content/70">No playlists yet. Create one below.</p>
			{:else}
				{#each playlists as playlist (playlist.id)}
					<label class="flex cursor-pointer items-center gap-3 rounded p-2 hover:bg-base-200">
						<input
							type="checkbox"
							class="checkbox checkbox-sm"
							checked={selectedIds.includes(playlist.id)}
							onchange={(e) =>
								toggleSelection(playlist.id, (e.currentTarget as HTMLInputElement).checked)}
						/>
						<div class="min-w-0 flex-1">
							<p class="truncate font-medium">{playlist.name}</p>
							{#if playlist.description}
								<p class="truncate text-xs text-base-content/60">{playlist.description}</p>
							{/if}
						</div>
					</label>
				{/each}
			{/if}
		</div>

		<form onsubmit={handleCreatePlaylist} class="rounded-box border border-base-300 p-3">
			<h4 class="mb-2 text-sm font-semibold">Create Playlist</h4>
			<div class="grid gap-2 md:grid-cols-[1fr_1fr_auto] md:items-end">
				<input
					type="text"
					class="input-bordered input input-sm w-full"
					placeholder="Playlist name"
					bind:value={newName}
					required
					disabled={isCreating || isSaving}
				/>
				<input
					type="text"
					class="input-bordered input input-sm w-full"
					placeholder="Description (optional)"
					bind:value={newDescription}
					disabled={isCreating || isSaving}
				/>
				<button
					class="btn btn-sm"
					type="submit"
					disabled={isCreating || !newName.trim() || isSaving}
				>
					{#if isCreating}<span class="loading loading-xs loading-spinner"></span>{/if}
					Create
				</button>
			</div>
		</form>

		<div class="mt-4 rounded-box border border-base-300 p-3">
			<h4 class="mb-2 text-sm font-semibold">Tags</h4>
			{#if tags.length === 0}
				<p class="text-sm text-base-content/60">Create tags in Settings to organize videos.</p>
			{:else}
				<div class="flex flex-wrap gap-2">
					{#each tags as tag (tag.id)}
						<label class="label cursor-pointer gap-2 rounded border border-base-300 px-2 py-1">
							<input
								type="checkbox"
								class="checkbox checkbox-xs"
								checked={selectedTagIds.includes(tag.id)}
								onchange={(event) => toggleTag(tag.id, event.currentTarget.checked)}
							/>
							<span class="label-text">{tag.name}</span>
						</label>
					{/each}
				</div>
			{/if}
		</div>

		{#if error}
			<p class="mt-3 text-sm text-error">{error}</p>
		{/if}

		<div class="modal-action">
			<button class="btn btn-ghost" onclick={onClose} disabled={isSaving || isCreating}
				>Cancel</button
			>
			<button
				class="btn btn-primary"
				onclick={() => void handleSave()}
				disabled={isSaving || isCreating}
			>
				{#if isSaving}<span class="loading loading-sm loading-spinner"></span>{/if}
				Save
			</button>
		</div>
	</div>
	<form method="dialog" class="modal-backdrop">
		<button type="button" onclick={onClose} aria-label="Close modal">close</button>
	</form>
</dialog>
