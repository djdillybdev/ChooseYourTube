<script lang="ts">
	import { resolve } from '$app/paths';
	import { uiState, toggleSidebar, closeMobileSidebar } from '$lib/stores/uiState.svelte';
	import type { CategoryOut, ChannelOut } from '$lib/types/api';
	import CategoryTree from './CategoryTree.svelte';
	import { openAddChannel, openCreateCategory } from '$lib/stores/modalState.svelte';
	import { afterNavigate } from '$app/navigation';

	interface Props {
		categories?: CategoryOut[];
		uncategorizedChannels?: ChannelOut[];
		channels?: ChannelOut[];
		backgroundJobsEnabled?: boolean;
		demoMode?: boolean;
	}

	let {
		categories = [],
		uncategorizedChannels = [],
		channels = [],
		backgroundJobsEnabled = true,
		demoMode = false
	}: Props = $props();

	const orderedCategories = $derived(
		[...categories].sort((left, right) => left.name.localeCompare(right.name))
	);
	const channelById = $derived(new Map(channels.map((channel) => [channel.id, channel])));
	function channelsFor(category: CategoryOut): ChannelOut[] {
		return (category.channel_ids ?? [])
			.map((id) => channelById.get(id))
			.filter((channel): channel is ChannelOut => channel !== undefined)
			.sort((left, right) => left.title.localeCompare(right.title));
	}
	const orderedUncategorized = $derived(
		[...uncategorizedChannels].sort((left, right) => left.title.localeCompare(right.title))
	);
	afterNavigate(closeMobileSidebar);
	let closeButton = $state<HTMLButtonElement>();
	$effect(() => {
		if (uiState.current.mobileSidebarOpen) queueMicrotask(() => closeButton?.focus());
	});
</script>

<svelte:window
	onkeydown={(event) => {
		if (event.key === 'Escape' && uiState.current.mobileSidebarOpen) closeMobileSidebar();
	}}
/>

{#if uiState.current.mobileSidebarOpen}
	<button class="sidebar-backdrop" aria-label="Close navigation" onclick={closeMobileSidebar}
	></button>
{/if}

<aside
	class="sidebar flex h-full flex-col border-r border-base-300 bg-base-100 transition-all duration-300"
	class:collapsed={uiState.current.sidebarCollapsed}
	class:mobile-open={uiState.current.mobileSidebarOpen}
	aria-label="Primary navigation"
	style="width: {uiState.current.sidebarCollapsed ? '0' : uiState.current.sidebarWidth}px;"
>
	{#if !uiState.current.sidebarCollapsed || uiState.current.mobileSidebarOpen}
		<div class="flex h-full flex-col overflow-hidden">
			<!-- Header -->
			<div class="flex items-center justify-between border-b border-base-300 p-4">
				<h2 class="text-lg font-bold">ChooseYourTube</h2>
				<button
					bind:this={closeButton}
					class="btn btn-square btn-ghost btn-sm"
					onclick={() =>
						uiState.current.mobileSidebarOpen ? closeMobileSidebar() : toggleSidebar()}
					aria-label={uiState.current.mobileSidebarOpen ? 'Close navigation' : 'Collapse sidebar'}
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
						<a href={resolve('/inbox')} class="flex items-center gap-2">
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
						<a href={resolve('/playlists')} class="flex items-center gap-2">
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

					<li>
						<a href={resolve('/watch-later')} class="flex items-center gap-2">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M17.25 6.75v12L12 15.75 6.75 18.75v-12A2.25 2.25 0 019 4.5h6a2.25 2.25 0 012.25 2.25z"
								/>
							</svg>
							<span>Watch Later</span>
						</a>
					</li>

					<!-- Settings -->
					<li>
						<a href={resolve('/settings')} class="flex items-center gap-2">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M4 6h16M4 12h16M4 18h10"
								/>
							</svg>
							<span>Settings</span>
							{#if !backgroundJobsEnabled}
								<span class="badge badge-ghost badge-xs">Demo</span>
							{/if}
						</a>
					</li>

					<!-- Categories Section -->
					<li class="mt-4 menu-title text-base-content/90">
						<span>Categories</span>
					</li>

					{#if orderedCategories.length === 0}
						<li class="text-sm text-base-content/90">
							<span>No categories yet</span>
						</li>
					{:else}
						{#each orderedCategories as category (category.id)}
							<CategoryTree {category} channels={channelsFor(category)} />
						{/each}
					{/if}

					<li class="mt-2">
						<button
							class="btn w-full justify-start gap-2 btn-ghost btn-sm"
							onclick={openCreateCategory}
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
							<span>New Category</span>
						</button>
					</li>

					<CategoryTree label="Uncategorized" channels={orderedUncategorized} />
				</ul>
			</nav>

			<!-- Footer Actions -->
			{#if !demoMode}<div class="border-t border-base-300 p-4">
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
				</div>{/if}
		</div>
	{/if}
</aside>

<style>
	.sidebar.collapsed {
		width: 0 !important;
		overflow: hidden;
	}
	.sidebar-backdrop {
		position: fixed;
		inset: 0;
		z-index: 39;
		background: rgb(0 0 0 / 45%);
	}
	@media (max-width: 767px) {
		.sidebar {
			position: fixed;
			inset: 0 auto 0 0;
			z-index: 40;
			width: min(88vw, 320px) !important;
			transform: translateX(-100%);
		}
		.sidebar.mobile-open {
			transform: translateX(0);
		}
		.sidebar.collapsed {
			width: min(88vw, 320px) !important;
		}
	}
</style>
