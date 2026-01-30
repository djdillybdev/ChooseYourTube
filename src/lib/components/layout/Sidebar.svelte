<script lang="ts">
	import { uiState, toggleSidebar } from '$lib/stores/uiState.svelte';
	import type { FolderOut } from '$lib/types/api';
	import AddChannelModal from '$lib/components/modals/AddChannelModal.svelte';
	import CreateFolderModal from '$lib/components/modals/CreateFolderModal.svelte';

	interface Props {
		folders?: FolderOut[];
	}

	let { folders = [] }: Props = $props();

	let showAddChannelModal = $state(false);
	let showCreateFolderModal = $state(false);

	function openAddChannelModal() {
		showAddChannelModal = true;
	}

	function closeAddChannelModal() {
		showAddChannelModal = false;
	}

	function openCreateFolderModal() {
		showCreateFolderModal = true;
	}

	function closeCreateFolderModal() {
		showCreateFolderModal = false;
	}
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
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M6 18L18 6M6 6l12 12"
						/>
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

					{#if folders.length === 0}
						<li class="text-sm text-base-content/60">
							<span>No folders yet</span>
						</li>
					{:else}
						{#each folders as folder}
							<li>
								<a href="/folders/{folder.id}" class="flex items-center gap-2">
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
									<span>{folder.name}</span>
								</a>
							</li>
						{/each}
					{/if}

					<!-- Add Folder Button -->
					<li class="mt-2">
						<button class="btn btn-ghost btn-sm w-full justify-start gap-2" onclick={openCreateFolderModal}>
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
				</ul>
			</nav>

			<!-- Footer Actions -->
			<div class="border-t border-base-300 p-4">
				<button class="btn btn-primary btn-sm w-full gap-2" onclick={openAddChannelModal}>
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

<!-- Modals -->
{#if showAddChannelModal}
	<AddChannelModal {folders} onClose={closeAddChannelModal} />
{/if}

{#if showCreateFolderModal}
	<CreateFolderModal {folders} onClose={closeCreateFolderModal} />
{/if}

<style>
	.sidebar.collapsed {
		width: 0 !important;
		overflow: hidden;
	}
</style>
