<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';

	interface Props {
		placeholder?: string;
		initialValue?: string;
		basePath: string;
	}

	let { placeholder = 'Search videos...', initialValue = '', basePath }: Props = $props();

	let searchQuery = $state('');
	let syncedInitialValue = $state<string | null>(null);
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;

	$effect(() => {
		if (initialValue !== syncedInitialValue) {
			searchQuery = initialValue;
			syncedInitialValue = initialValue;
		}
	});

	/**
	 * Debounced search input handler.
	 * Waits 300ms after user stops typing before updating URL.
	 */
	function handleInput(event: Event) {
		const target = event.target as HTMLInputElement;
		searchQuery = target.value;

		// Clear existing timer
		if (debounceTimer) {
			clearTimeout(debounceTimer);
		}

		// Set new timer
		debounceTimer = setTimeout(() => {
			updateSearchParam(searchQuery.trim());
		}, 300);
	}

	/**
	 * Updates URL with q parameter and resets to page 1.
	 * Preserves other URL params like pageSize.
	 */
	function updateSearchParam(query: string) {
		const url = new URL(window.location.href);

		if (query) {
			url.searchParams.set('q', query);
		} else {
			url.searchParams.delete('q');
		}

		// Reset to page 1 when search changes (new search = new result set)
		url.searchParams.set('page', '1');

		// Use keepFocus to prevent input blur during navigation
		goto(resolve(`${basePath}${url.search}` as '/inbox'), { keepFocus: true });
	}

	/**
	 * Clear search input and remove search param from URL.
	 */
	function clearSearch() {
		searchQuery = '';
		updateSearchParam('');
	}
</script>

<div class="relative w-full">
	<div class="relative">
		<!-- Search icon -->
		<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
				class="h-5 w-5 text-base-content/40"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
				/>
			</svg>
		</div>

		<!-- Search input -->
		<input
			type="text"
			class="input-bordered input w-full pr-10 pl-10"
			{placeholder}
			bind:value={searchQuery}
			oninput={handleInput}
			maxlength="100"
		/>

		<!-- Clear button (only shown when text is present) -->
		{#if searchQuery}
			<button
				type="button"
				class="btn absolute inset-y-0 right-1 my-auto btn-circle btn-ghost btn-sm"
				onclick={clearSearch}
				aria-label="Clear search"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					class="h-4 w-4"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		{/if}
	</div>
</div>
