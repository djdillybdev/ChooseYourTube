<script lang="ts">
	import { uiState, toggleSidebar } from '$lib/stores/uiState.svelte';
	import type { FolderOut, ChannelOut } from '$lib/types/api';
	import FolderTree from './FolderTree.svelte';
	import { openAddChannel, openCreateFolder, openEditChannel } from '$lib/stores/modalState.svelte';
	import { api } from '$lib/api';

	interface Props {
		folders?: FolderOut[];
		unfolderedChannels?: ChannelOut[];
	}

	let { folders = [], unfolderedChannels = [] }: Props = $props();

	// Filter to only root folders (FolderTree handles children recursively)
	const rootFolders = $derived(folders.filter((f) => f.parent_id === null));

	// Load all channels for passing to FolderTree
	let allChannels: ChannelOut[] = $state([]);

	async function loadAllChannels() {
		try {
			const channels: ChannelOut[] = [];
			let response = await api.channels.list();
			do {
				channels.push(...response.items);
				if (!response.has_more) break;
				response = await api.channels.list({
					limit: response.limit,
					offset: response.offset + response.limit
				});
			} while (response.has_more);
			allChannels = channels;
		} catch (err) {
			console.error('Failed to load channels:', err);
			allChannels = unfolderedChannels; // Fallback to unfoldered only
		}
	}

	$effect(() => {
		void unfolderedChannels; // Re-trigger when layout data changes
		loadAllChannels();
	});
</script>

<aside
	class="sidebar flex h-full flex-col border-r border-base-300 bg-base-100 transition-all duration-300"
	class:collapsed={uiState.current.sidebarCollapsed}
	style="width: {uiState.current.sidebarCollapsed ? '0' : uiState.current.sidebarWidth}px;"
>
	{#if !uiState.current.sidebarCollapsed}
		<div class="flex h-full flex-col overflow-hidden">
			<!-- Header -->
			<div class="flex items-center justify-between border-b border-base-300 p-4">
				<h2 class="text-lg font-bold">ChooseYourTube</h2>
				<button
					class="btn btn-square btn-ghost btn-sm"
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

					<!-- Playlists -->
					<li>
						<a href="/playlists" class="flex items-center gap-2">
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
									d="M9 9l10.5-3m0 0L21 16.5M19.5 6L9 9m0 0l-1.5 10.5M9 9L3 7.5m4.5 12L3 7.5m0 0L13.5 4.5"
								/>
							</svg>
							<span>Playlists</span>
						</a>
					</li>

					<!-- Folders Section -->
					<li class="mt-4 menu-title">
						<span>Folders</span>
					</li>

					{#if rootFolders.length === 0}
						<li class="text-sm text-base-content/60">
							<span>No folders yet</span>
						</li>
					{:else}
						{#each rootFolders as folder (folder.id)}
							<FolderTree {folder} {allChannels} />
						{/each}
					{/if}

					<!-- Add Folder Button -->
					<li class="mt-2">
						<button
							class="btn w-full justify-start gap-2 btn-ghost btn-sm"
							onclick={openCreateFolder}
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
					<li class="mt-4 menu-title">
						<span>Channels</span>
					</li>

					{#if unfolderedChannels.length === 0}
						<li class="text-sm text-base-content/60">
							<span>No channels yet</span>
						</li>
						{:else}
							{#each unfolderedChannels as channel (channel.id)}
								<li class="group">
									<div class="channel-item flex items-center">
										<a href="/channels/{channel.id}" class="flex flex-1 items-center gap-2">
										{#if channel.thumbnail_url}
											<img
												src={channel.thumbnail_url}
												alt={channel.title}
												class="h-5 w-5 shrink-0 rounded-full object-cover"
											/>
										{:else}
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
										{/if}
										<span>{channel.title}</span>
									</a>

										<button
											class="btn btn-square btn-ghost btn-xs opacity-0 pointer-events-none transition-opacity group-hover:opacity-100 group-hover:pointer-events-auto group-focus-within:opacity-100 group-focus-within:pointer-events-auto"
											onclick={(e) => {
												e.stopPropagation();
												openEditChannel(channel);
											}}
											aria-label="Edit channel"
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 24 24"
												fill="currentColor"
												class="h-4 w-4"
											>
												<path
													d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM11.25 18.75a.75.75 0 111.5 0 .75.75 0 01-1.5 0z"
												/>
											</svg>
										</button>
									</div>
								</li>
							{/each}
					{/if}
				</ul>
			</nav>

			<!-- Footer Actions -->
			<div class="border-t border-base-300 p-4">
				<button class="btn w-full gap-2 btn-sm btn-primary" onclick={openAddChannel}>
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
