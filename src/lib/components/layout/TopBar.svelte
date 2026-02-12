<script lang="ts">
	import { uiState, toggleSidebar } from '$lib/stores/uiState.svelte';
	import { filterState, setWatchedFilter } from '$lib/stores/filterState.svelte';
</script>

<header class="flex h-16 items-center justify-between border-b border-base-300 bg-base-100 px-4">
	<!-- Left: Sidebar toggle (if collapsed) -->
	<div class="flex items-center gap-2">
		{#if uiState.current.sidebarCollapsed}
			<button
				class="btn btn-square btn-ghost btn-sm"
				onclick={toggleSidebar}
				aria-label="Open sidebar"
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
						d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
					/>
				</svg>
			</button>
		{/if}
	</div>

	<!-- Center: Filter controls -->
	<div class="flex items-center gap-2">
		<!-- Watch status filter -->
		<div class="join">
			<button
				class="btn join-item btn-sm"
				class:btn-active={filterState.current.is_watched === undefined}
				onclick={() => setWatchedFilter(undefined)}
			>
				All
			</button>
			<button
				class="btn join-item btn-sm"
				class:btn-active={filterState.current.is_watched === false}
				onclick={() => setWatchedFilter(false)}
			>
				Unwatched
			</button>
			<button
				class="btn join-item btn-sm"
				class:btn-active={filterState.current.is_watched === true}
				onclick={() => setWatchedFilter(true)}
			>
				Watched
			</button>
		</div>
	</div>

	<!-- Right: Actions -->
	<div class="flex items-center gap-2">
		<!-- Refresh button -->
		<button class="btn btn-square btn-ghost btn-sm" aria-label="Refresh">
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
					d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
				/>
			</svg>
		</button>
	</div>
</header>
