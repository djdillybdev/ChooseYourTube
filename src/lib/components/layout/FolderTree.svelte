<script lang="ts">
	import type { ChannelOut, FolderOut } from '$lib/types/api';
	import { folderExpansion } from '$lib/stores/folderExpansion.svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api';
	import { dndzone, type DndEvent } from 'svelte-dnd-action';
	import { flip } from 'svelte/animate';
	import type { Channel } from 'diagnostics_channel';
	import { openEditFolder } from '$lib/stores/modalState.svelte';

	interface Props {
		folder: FolderOut;
		depth?: number;
	}

	let { folder, depth = 0 }: Props = $props();

	const hasChildren = $derived(folder.children && folder.children.length > 0);
	const isExpanded = $derived(folderExpansion.isExpanded(folder.id));
	const isActive = $derived($page.params.id === folder.id.toString());

	// Local state for dnd-action (must be a flat array of objects with 'id')
	// We sync this with folder.children when props change
	let items: (FolderOut | ChannelOut)[] = $state(folder.children || []);
	$effect(() => {
		items = folder.children || [];
	});

	// Edit mode state
	let isEditing = $state(false);
	let editedName = $state(folder.name);
	let inputElement: HTMLInputElement | undefined = $state();
	let allowBlur = $state(false);

	// Focus and select input when entering edit mode
	$effect(() => {
		if (isEditing && inputElement) {
			inputElement.focus();
			inputElement.select();
			// Allow blur to cancel after input is focused
			setTimeout(() => {
				allowBlur = true;
			}, 100);
		}
	});

	function toggleExpand(e: MouseEvent) {
		e.preventDefault();
		e.stopPropagation();
		folderExpansion.toggle(folder.id);
	}

	// Drag-and-drop handlers
	const flipDurationMs = 200;

	function handleDndConsider(e: CustomEvent<DndEvent<FolderOut | ChannelOut>>) {
		items = e.detail.items;
	}

	async function handleDndFinalize(e: CustomEvent<DndEvent<FolderOut | ChannelOut>>) {
		items = e.detail.items;
		const { info } = e.detail;

		if (info.trigger !== 'droppedIntoZone') return;

		const droppedId = info.id;

		const droppedItem = items.find(i => i.id === droppedId);
		const isChannel = droppedItem && 'title' in droppedItem;

		if (isChannel) {
			// Update channel's folder_id
			try {
				await api.channels.update(droppedId, { folder_id: folder.id });
				api.invalidate('/channels');
			} catch (error) {
				console.error('Failed to move channel to folder:', error);
			}
		}
	}

	// Start editing folder name

	function startEditing(e: MouseEvent) {
		console.log('Starting edit mode for folder:', folder.name);
		allowBlur = false;
		isEditing = true;
		editedName = folder.name;
	}

	function handleBlur() {
		// Only cancel if we've given the input time to focus
		if (allowBlur) {
			cancelEdit();
		}
	}

	function cancelEdit() {
		isEditing = false;
		editedName = folder.name;
		allowBlur = false;
	}

	async function saveEdit() {
		const trimmedName = editedName.trim();

		// Validate name is not empty
		if (!trimmedName) {
			cancelEdit();
			return;
		}

		// If name hasn't changed, just exit edit mode
		if (trimmedName === folder.name) {
			isEditing = false;
			return;
		}

		// Optimistic update
		const originalName = folder.name;
		folder.name = trimmedName;
		isEditing = false;

		try {
			await api.folders.update(folder.id, { name: trimmedName });
			api.invalidate('/folders');
		} catch (error) {
			// Revert on error
			folder.name = originalName;
			console.error('Failed to update folder name:', error);
			// TODO: Show error toast
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		// Handle Enter and Escape keys
		if (e.key === 'Enter') {
			saveEdit();
		} else if (e.key === 'Escape') {
			cancelEdit();
		}
	}
</script>

<li>
	<div class="group flex items-center" style="padding-left: {depth * 1}rem">
		<!-- Chevron button (only if folder has children) -->
		{#if hasChildren}
			<button
				onclick={toggleExpand}
				class="btn btn-ghost btn-xs mr-1 p-0 hover:bg-transparent"
				aria-label={isExpanded ? 'Collapse folder' : 'Expand folder'}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="chevron h-4 w-4 transition-transform duration-200"
					class:rotate-90={isExpanded}
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
				</svg>
			</button>
		{:else}
			<!-- Spacer to maintain alignment when no chevron -->
			<span class="mr-1 w-4"></span>
		{/if}

		<!-- Folder link (disabled when editing) -->
		{#if isEditing}
			<div class="flex flex-1 items-center gap-2 rounded px-2 py-1.5" class:bg-base-200={isActive}>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="h-5 w-5"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
					/>
				</svg>
				<!-- Edit mode: input field -->
				<input
					bind:this={inputElement}
					bind:value={editedName}
					onkeydown={handleKeydown}
					onblur={handleBlur}
					type="text"
					class="input input-xs flex-1 px-1 text-sm"
				/>
			</div>
		{:else}
			<a
				href="/folders/{folder.id}"
				class="hover:bg-base-200 flex flex-1 items-center gap-2 rounded px-2 py-1.5 transition-colors"
				class:bg-base-200={isActive}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="h-5 w-5"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
					/>
				</svg>
				<!-- Normal mode: editable text -->
				<span class="cursor-text text-sm" ondblclick={startEditing} role="button" tabindex="0">
					{folder.name}
				</span>
			</a>
		{/if}

		<!-- Three-dot menu button (hover-reveal) -->
		{#if !isEditing}
			<button
				class="opacity-0 group-hover:opacity-100 btn btn-ghost btn-xs btn-square transition-opacity"
				onclick={(e) => { e.stopPropagation(); openEditFolder(folder); }}
				aria-label="Edit folder"
			>
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-4 w-4">
					<path d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM11.25 18.75a.75.75 0 111.5 0 .75.75 0 01-1.5 0z" />
				</svg>
			</button>
		{/if}
	</div>

	<!-- Recursively render children when expanded -->
	{#if hasChildren && isExpanded}
		<ul class="mt-1">
			{#each folder.children as child}
				<svelte:self folder={child} depth={depth + 1} />
			{/each}
		</ul>
	{/if}
</li>

<style>
	.chevron {
		transform: rotate(0deg);
	}

	.chevron.rotate-90 {
		transform: rotate(90deg);
	}
</style>
