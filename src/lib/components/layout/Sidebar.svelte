<script lang="ts">
	import { uiState, toggleSidebar } from '$lib/stores/uiState.svelte';
	import type { FolderOut, ChannelOut } from '$lib/types/api';
	import FolderTree from './FolderTree.svelte';

	interface Props {
		folders?: FolderOut[];
		unfolderedChannels?: ChannelOut[];
		onOpenAddChannel?: () => void;
		onOpenCreateFolder?: () => void;
	}

	let {
		folders = [],
		unfolderedChannels = [],
		onOpenAddChannel,
		onOpenCreateFolder
	}: Props = $props();

	// Filter to only root folders (FolderTree handles children recursively)
	const rootFolders = $derived(folders.filter((f) => f.parent_id === null));
</script>

<aside
	class="sidebar border-base-300 bg-base-100 flex h-full flex-col border-r transition-all duration-300"
	class:collapsed={uiState.current.sidebarCollapsed}
	style="width: {uiState.current.sidebarCollapsed ? '0' : uiState.current.sidebarWidth}px;"
>
	{#if !uiState.current.sidebarCollapsed}
		<div class="flex h-full flex-col overflow-hidden">
			<!-- Header -->
			<div class="border-base-300 flex items-center justify-between border-b p-4">
				<h2 class="text-lg font-bold">ChooseYourTube</h2>
				<button
					class="btn btn-ghost btn-sm btn-square"
					onclick={toggleSidebar}
					aria-label="Collapse sidebar"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="h-5 w-5"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<!-- Navigation -->
			<nav class="flex-1 overflow-y-auto p-4">
				<ul class="menu">
					<!-- Inbox -->
					<li>
						<a href="/inbox" class="flex items-center gap-2">
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
									d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z"
								/>
							</svg>
							<span>Inbox</span>
						</a>
					</li>

					<!-- Folders Section -->
					<li class="menu-title mt-4">
						<span>Folders</span>
					</li>

					{#if rootFolders.length === 0}
						<li class="text-base-content/60 text-sm">
							<span>No folders yet</span>
						</li>
					{:else}
						{#each rootFolders as folder}
							<FolderTree {folder} />
						{/each}
					{/if}

					<!-- Add Folder Button -->
					<li class="mt-2">
						<button
							class="btn btn-ghost btn-sm w-full justify-start gap-2"
							onclick={onOpenCreateFolder}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="h-5 w-5"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
							</svg>
							<span>New Folder</span>
						</button>
					</li>

					<!-- Channels Section -->
					<li class="menu-title mt-4">
						<span>Channels</span>
					</li>

					{#if unfolderedChannels.length === 0}
						<li class="text-base-content/60 text-sm">
							<span>No channels yet</span>
						</li>
					{:else}
						{#each unfolderedChannels as channel}
							<li>
								<a href="/channels/{channel.id}" class="flex items-center gap-2">
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
											d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"
										/>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"
										/>
									</svg>
									<span>{channel.title}</span>
								</a>
							</li>
						{/each}
					{/if}
				</ul>
			</nav>

			<!-- Footer Actions -->
			<div class="border-base-300 border-t p-4">
				<button class="btn btn-primary btn-sm w-full gap-2" onclick={onOpenAddChannel}>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="h-5 w-5"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
					</svg>
					<span>Add Channel</span>
				</button>
			</div>
		</div>
	{/if}
</aside>

<style>
	.sidebar.collapsed {
		width: 0 !important;
		overflow: hidden;
	}
</style>
