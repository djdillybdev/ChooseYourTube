<script lang="ts">
	import { invalidate } from '$app/navigation';
	import { api } from '$lib/api';
	import type { PageData } from './$types';
	import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let newName = $state('');
	let editingId = $state<string | null>(null);
	let editingName = $state('');
	let busyId = $state<string | null>(null);
	let error = $state<string | null>(null);
	let pendingDelete = $state<{
		id: string;
		name: string;
		channels: number;
		videos: number;
	} | null>(null);

	async function refreshTags() {
		await invalidate('app:tags');
	}

	async function createTag(event: SubmitEvent) {
		event.preventDefault();
		if (!newName.trim()) return;
		busyId = 'new';
		error = null;
		try {
			await api.tags.create({ name: newName });
			newName = '';
			await refreshTags();
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Could not create tag.';
		} finally {
			busyId = null;
		}
	}

	function beginRename(id: string, name: string) {
		editingId = id;
		editingName = name;
		error = null;
	}

	async function renameTag(id: string) {
		if (!editingName.trim()) return;
		busyId = id;
		error = null;
		try {
			await api.tags.update(id, { name: editingName });
			editingId = null;
			await refreshTags();
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Could not rename tag.';
		} finally {
			busyId = null;
		}
	}

	async function deleteTag(id: string) {
		busyId = id;
		error = null;
		try {
			await api.tags.delete(id);
			pendingDelete = null;
			await refreshTags();
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Could not delete tag.';
		} finally {
			busyId = null;
		}
	}
</script>

<svelte:head><title>Organization - Settings - ChooseYourTube</title></svelte:head>

<div class="container mx-auto max-w-6xl p-6 pt-5">
	<section class="rounded-box border border-base-300 bg-base-100 p-5">
		<div class="mb-4">
			<h2 class="text-xl font-semibold">Tags</h2>
			<p class="text-sm text-base-content/60">Tags organize channels and videos across folders.</p>
		</div>

		<form class="mb-5 flex max-w-xl gap-2" onsubmit={createTag}>
			<label class="sr-only" for="new-tag">Tag name</label>
			<input
				id="new-tag"
				class="input-bordered input flex-1"
				placeholder="New tag"
				maxlength="255"
				bind:value={newName}
				disabled={busyId === 'new'}
			/>
			<button class="btn btn-primary" disabled={!newName.trim() || busyId === 'new'}>
				{busyId === 'new' ? 'Creating…' : 'Create tag'}
			</button>
		</form>

		{#if error}<div class="mb-4 alert alert-error" role="alert">{error}</div>{/if}

		{#if data.tags.length === 0}
			<div class="rounded-box bg-base-200 p-8 text-center text-base-content/60">
				No tags yet. Create one to categorize channels and videos.
			</div>
		{:else}
			<div class="overflow-x-auto">
				<table class="table">
					<thead
						><tr
							><th>Name</th><th>Channels</th><th>Videos</th><th class="text-right">Actions</th></tr
						></thead
					>
					<tbody>
						{#each data.tags as tag (tag.id)}
							<tr>
								<td>
									{#if editingId === tag.id}
										<input
											class="input-bordered input input-sm"
											maxlength="255"
											bind:value={editingName}
										/>
									{:else}<span class="font-medium">{tag.name}</span>{/if}
								</td>
								<td>{tag.channel_count}</td>
								<td>{tag.video_count}</td>
								<td class="text-right">
									{#if editingId === tag.id}
										<button
											class="btn btn-xs btn-primary"
											disabled={!editingName.trim() || busyId === tag.id}
											onclick={() => void renameTag(tag.id)}>Save</button
										>
										<button class="btn btn-ghost btn-xs" onclick={() => (editingId = null)}
											>Cancel</button
										>
									{:else}
										<button
											class="btn btn-ghost btn-xs"
											onclick={() => beginRename(tag.id, tag.name)}>Rename</button
										>
										<button
											class="btn text-error btn-ghost btn-xs"
											disabled={busyId === tag.id}
											onclick={() =>
												(pendingDelete = {
													id: tag.id,
													name: tag.name,
													channels: tag.channel_count,
													videos: tag.video_count
												})}>Delete</button
										>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</section>
</div>

{#if pendingDelete}
	<ConfirmDialog
		title="Delete tag?"
		message={`“${pendingDelete.name}” will be removed from ${pendingDelete.channels} channel${pendingDelete.channels === 1 ? '' : 's'} and ${pendingDelete.videos} video${pendingDelete.videos === 1 ? '' : 's'}.`}
		confirmLabel="Delete tag"
		busy={busyId === pendingDelete.id}
		{error}
		onConfirm={() => deleteTag(pendingDelete!.id)}
		onCancel={() => (pendingDelete = null)}
	/>
{/if}
