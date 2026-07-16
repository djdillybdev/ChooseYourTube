<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { uiState, toggleSidebar, openMobileSidebar } from '$lib/stores/uiState.svelte';
	import { authState } from '$lib/stores/authState.svelte';
	import type { ChannelOut, TagOut, UserRead } from '$lib/types/api';
	import VideoFilters from '$lib/components/video/VideoFilters.svelte';

	interface Props {
		channels?: ChannelOut[];
		tags?: TagOut[];
		currentUser?: UserRead | null;
	}

	let { channels = [], tags = [], currentUser = null }: Props = $props();

	const path = $derived(page.url.pathname);
	const isVideoListPage = $derived(
		path === '/inbox' ||
			path === '/favorites' ||
			/^\/channels\/[^/]+$/.test(path) ||
			path.startsWith('/folders/') ||
			path.startsWith('/categories/')
	);

	async function handleLogout() {
		await authState.logout();
		goto(resolve('/login'), { replaceState: true });
	}
</script>

<header
	class="flex h-16 items-center justify-between border-b border-base-300 bg-base-100 px-2 sm:px-4"
>
	<div class="flex shrink-0 items-center gap-2">
		<button
			id="mobile-nav-trigger"
			class="btn btn-square btn-ghost btn-sm md:hidden"
			onclick={openMobileSidebar}
			aria-label="Open navigation"
		>
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5" aria-hidden="true">
				<path stroke-linecap="round" stroke-width="1.5" d="M4 6h16M4 12h16M4 18h16" />
			</svg>
		</button>
		{#if uiState.current.sidebarCollapsed}
			<button
				class="btn hidden btn-square btn-ghost btn-sm md:inline-flex"
				onclick={toggleSidebar}
				aria-label="Open sidebar"
			>
				<svg
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					class="h-5 w-5"
					aria-hidden="true"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="1.5"
						d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
					/>
				</svg>
			</button>
		{/if}
	</div>

	{#if isVideoListPage}
		<div class="flex min-w-0 flex-1 items-center justify-center px-1 sm:px-4">
			<VideoFilters {channels} {tags} currentPath={path} />
		</div>
	{:else}
		<div class="min-w-0 flex-1"></div>
	{/if}

	<div class="flex shrink-0 items-center gap-1 sm:gap-2">
		{#if currentUser}
			<span
				class="hidden max-w-48 truncate text-sm text-base-content/90 lg:inline"
				title={currentUser.email}
			>
				{currentUser.email}
			</span>
		{/if}
		<button class="btn btn-ghost btn-sm" aria-label="Log out" onclick={handleLogout}>
			<span class="hidden sm:inline">Log out</span>
			<svg
				class="h-5 w-5 sm:hidden"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				aria-hidden="true"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="1.5"
					d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3-3H9m9.75 0l-3-3m3 3l-3 3"
				/>
			</svg>
		</button>
	</div>
</header>
