<script lang="ts">
	import type { ChannelOut, FolderOut } from '$lib/types/api';
	import { folderExpansion } from '$lib/stores/folderExpansion.svelte';
	import { page } from '$app/stores';
	import ChannelTreeItem from './ChannelTreeItem.svelte';

	interface Props {
		folder: FolderOut;
		allChannels: ChannelOut[];
		depth?: number;
	}

	let { folder, allChannels, depth = 0 }: Props = $props();

	// Filter channels that belong to this folder
	const channelsInFolder = $derived(allChannels.filter((ch) => ch.folder_id === folder.id));

	const hasChildren = $derived(
		(folder.children && folder.children.length > 0) || channelsInFolder.length > 0
	);
	const isExpanded = $derived(folderExpansion.isExpanded(folder.id));
	const isActive = $derived($page.params.id === folder.id.toString());

	function toggleExpand(e: MouseEvent) {
		e.preventDefault();
		e.stopPropagation();
		folderExpansion.toggle(folder.id);
	}
</script>

<li>
	<div
		class="folder-item flex items-center"
		style="padding-left: {depth * 1}rem"
	>
		<!-- Chevron button (only if folder has children) -->
		{#if hasChildren}
			<button
				onclick={toggleExpand}
				class="btn mr-1 p-0 btn-ghost btn-xs hover:bg-transparent"
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

		<!-- Folder link -->
		<a
			href="/folders/{folder.id}"
			class="flex flex-1 items-center gap-2 rounded px-2 py-1.5 transition-colors"
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
			<span class="text-sm">{folder.name}</span>
		</a>
	</div>

	{#if hasChildren && isExpanded}
		<ul class="mt-1">
			{#each folder.children ?? [] as childFolder (childFolder.id)}
				<svelte:self folder={childFolder} {allChannels} depth={depth + 1} />
			{/each}
			{#each channelsInFolder as channel (channel.id)}
				<ChannelTreeItem {channel} depth={depth + 1} />
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
