<script lang="ts">
	import { resolve } from '$app/paths';
	import { uiState, toggleSidebar, closeMobileSidebar } from '$lib/stores/uiState.svelte';
	import type { CategoryOut, ChannelOut } from '$lib/types/api';
	import CategoryTree from './CategoryTree.svelte';
	import { openAddChannel, openCreateCategory } from '$lib/stores/modalState.svelte';
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/state';

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
	let channelQuery = $state('');
	const normalizedChannelQuery = $derived(channelQuery.trim().toLocaleLowerCase());
	function channelMatches(channel: ChannelOut): boolean {
		return (
			!normalizedChannelQuery || channel.title.toLocaleLowerCase().includes(normalizedChannelQuery)
		);
	}
	function isCurrent(path: string, exact = false): boolean {
		return exact ? page.url.pathname === path : page.url.pathname.startsWith(path);
	}

	const orderedCategories = $derived(
		[...categories].sort((left, right) => left.name.localeCompare(right.name))
	);
	const channelById = $derived(new Map(channels.map((channel) => [channel.id, channel])));
	function channelsFor(category: CategoryOut): ChannelOut[] {
		return (category.channel_ids ?? [])
			.map((id) => channelById.get(id))
			.filter((channel): channel is ChannelOut => channel !== undefined)
			.filter(channelMatches)
			.sort((left, right) => left.title.localeCompare(right.title));
	}
	const visibleCategories = $derived(
		normalizedChannelQuery
			? orderedCategories.filter((category) => channelsFor(category).length > 0)
			: orderedCategories
	);
	const orderedUncategorized = $derived(
		[...uncategorizedChannels]
			.filter(channelMatches)
			.sort((left, right) => left.title.localeCompare(right.title))
	);
	const matchingChannelCount = $derived(channels.filter(channelMatches).length);
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
			<nav class="min-w-0 flex-1 overflow-x-hidden overflow-y-auto p-4" aria-label="Primary">
				<ul class="sidebar-menu menu w-full max-w-full min-w-0 flex-nowrap overflow-x-hidden">
					<!-- Inbox -->
					<li>
						<a
							href={resolve('/inbox')}
							class="sidebar-library-link flex w-full max-w-full min-w-0 items-center gap-2"
							class:bg-base-200={isCurrent('/inbox', true)}
							aria-current={isCurrent('/inbox', true) ? 'page' : undefined}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="h-5 w-5 shrink-0"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z"
								/>
							</svg>
							<span class="min-w-0 truncate">Inbox</span>
						</a>
					</li>

					<li>
						<a
							href={resolve('/favorites')}
							class="sidebar-library-link flex w-full max-w-full min-w-0 items-center gap-2"
							class:bg-base-200={isCurrent('/favorites', true)}
							aria-current={isCurrent('/favorites', true) ? 'page' : undefined}
						>
							<svg
								viewBox="0 0 24 24"
								fill={page.url.pathname === '/favorites' ? 'currentColor' : 'none'}
								stroke="currentColor"
								stroke-width="1.5"
								class="h-5 w-5 shrink-0"
								aria-hidden="true"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
								/>
							</svg>
							<span class="min-w-0 truncate">Favorites</span>
						</a>
					</li>

					<li>
						<a
							href={resolve('/queue')}
							class="sidebar-library-link flex w-full max-w-full min-w-0 items-center gap-2"
							class:bg-base-200={isCurrent('/queue', true)}
							aria-current={isCurrent('/queue', true) ? 'page' : undefined}
						>
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5 shrink-0">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M4.5 6.75h15m-15 5.25h15m-15 5.25h10.5"
								/>
							</svg>
							<span class="min-w-0 truncate">Queue</span>
						</a>
					</li>

					<!-- Playlists -->
					<li>
						<a
							href={resolve('/playlists')}
							class="sidebar-library-link flex w-full max-w-full min-w-0 items-center gap-2"
							class:bg-base-200={isCurrent('/playlists')}
							aria-current={isCurrent('/playlists') ? 'page' : undefined}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="h-5 w-5 shrink-0"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M9 9l10.5-3m0 0L21 16.5M19.5 6L9 9m0 0l-1.5 10.5M9 9L3 7.5m4.5 12L3 7.5m0 0L13.5 4.5"
								/>
							</svg>
							<span class="min-w-0 truncate">Playlists</span>
						</a>
					</li>

					<li>
						<a
							href={resolve('/watch-later')}
							class="sidebar-library-link flex w-full max-w-full min-w-0 items-center gap-2"
							class:bg-base-200={isCurrent('/watch-later', true)}
							aria-current={isCurrent('/watch-later', true) ? 'page' : undefined}
						>
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5 shrink-0">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M17.25 6.75v12L12 15.75 6.75 18.75v-12A2.25 2.25 0 019 4.5h6a2.25 2.25 0 012.25 2.25z"
								/>
							</svg>
							<span class="min-w-0 truncate">Watch Later</span>
						</a>
					</li>

					<!-- Settings -->
					<li>
						<a
							href={resolve('/settings')}
							class="sidebar-library-link flex w-full max-w-full min-w-0 items-center gap-2"
							class:bg-base-200={isCurrent('/settings')}
							aria-current={isCurrent('/settings') ? 'page' : undefined}
						>
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5 shrink-0">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M4 6h16M4 12h16M4 18h10"
								/>
							</svg>
							<span class="min-w-0 truncate">Settings</span>
							{#if !backgroundJobsEnabled}
								<span class="badge shrink-0 badge-ghost badge-xs">Demo</span>
							{/if}
						</a>
					</li>

					<!-- Categories Section -->
					<li class="mt-3 min-w-0 menu-title text-base-content/90">
						<span>Categories</span>
					</li>

					{#if channels.length >= 8}
						<li class="mb-1 min-w-0 px-1">
							<label for="sidebar-channel-search" class="sr-only">Find a followed channel</label>
							<input
								id="sidebar-channel-search"
								type="search"
								class="input input-sm w-full max-w-full min-w-0"
								placeholder="Find a channel"
								bind:value={channelQuery}
							/>
						</li>
					{/if}

					{#if orderedCategories.length === 0}
						<li class="text-sm text-base-content/90">
							<span>No categories yet</span>
						</li>
					{:else}
						{#each visibleCategories as category (category.id)}
							<CategoryTree {category} channels={channelsFor(category)} />
						{/each}
					{/if}

					<li class="mt-1 min-w-0">
						<button
							class="btn w-full max-w-full min-w-0 justify-start gap-2 overflow-hidden btn-ghost btn-sm"
							onclick={openCreateCategory}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="h-5 w-5 shrink-0"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
							</svg>
							<span class="min-w-0 truncate">New Category</span>
						</button>
					</li>

					<CategoryTree label="Uncategorized" channels={orderedUncategorized} />
					{#if normalizedChannelQuery && matchingChannelCount === 0}
						<li><p class="text-sm text-base-content/70">No matching channels.</p></li>
					{/if}
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
	.sidebar-menu {
		width: 100%;
		min-width: 0;
		max-width: 100%;
		flex-wrap: nowrap;
		overflow-x: hidden;
	}
	.sidebar-library-link {
		width: 100%;
		min-width: 0;
		max-width: 100%;
	}
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
