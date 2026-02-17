<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { uiState, toggleSidebar } from '$lib/stores/uiState.svelte';
	import type { ChannelOut, TagOut } from '$lib/types/api';
	import { parseVideoFilterQuery } from '$lib/utils/videoFilterQuery';

	interface Props {
		channels?: ChannelOut[];
		tags?: TagOut[];
	}

	let { channels = [], tags = [] }: Props = $props();

	const path = $derived(page.url.pathname);
	const isVideoListPage = $derived(
		path === '/inbox' || path.startsWith('/channels/') || path.startsWith('/folders/')
	);
	const isChannelDetailPage = $derived(path.startsWith('/channels/'));
	const { uiFilters } = $derived(
		parseVideoFilterQuery(page.url, { defaultWatched: path === '/inbox' ? false : undefined })
	);

	const sortOptions = [
		{ value: 'published_at', label: 'Published' },
		{ value: 'title', label: 'Title' },
		{ value: 'created_at', label: 'Added' },
		{ value: 'duration_seconds', label: 'Duration' },
		{ value: 'relevance', label: 'Relevance' }
	] as const;
	const extendedFilterCount = $derived(
		[
			uiFilters.is_favorited,
			uiFilters.is_short,
			uiFilters.channel_id,
			uiFilters.tag_id,
			uiFilters.published_after,
			uiFilters.published_before
		].filter((value) => value !== undefined && value !== '').length +
			(uiFilters.order_by && uiFilters.order_by !== 'published_at' ? 1 : 0) +
			(uiFilters.order_direction && uiFilters.order_direction !== 'desc' ? 1 : 0)
	);

	function updateQuery(mutator: (params: URLSearchParams) => void) {
		const url = new URL(page.url);
		mutator(url.searchParams);
		url.searchParams.set('page', '1');
		goto(url.pathname + url.search, { keepFocus: true, noScroll: true });
	}

	function setBooleanFilter(key: 'is_watched' | 'is_favorited' | 'is_short', value: boolean | undefined) {
		updateQuery((params) => {
			if (value === undefined) {
				params.delete(key);
			} else {
				params.set(key, String(value));
			}
		});
	}

	function setStringFilter(
		key: 'channel_id' | 'tag_id' | 'published_after' | 'published_before',
		value: string
	) {
		updateQuery((params) => {
			if (!value) {
				params.delete(key);
			} else {
				params.set(key, value);
			}
		});
	}

	function setSortFilter(key: 'order_by' | 'order_direction', value: string) {
		updateQuery((params) => {
			if (!value) {
				params.delete(key);
			} else {
				params.set(key, value);
			}
		});
	}

	function clearFilters() {
		updateQuery((params) => {
			for (const key of [
				'is_watched',
				'is_favorited',
				'is_short',
				'channel_id',
				'tag_id',
				'published_after',
				'published_before',
				'order_by',
				'order_direction'
			]) {
				params.delete(key);
			}
		});
	}
</script>

<header class="flex h-16 items-center justify-between border-b border-base-300 bg-base-100 px-4">
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

	{#if isVideoListPage}
		<div class="flex flex-1 items-center justify-center gap-2 px-4">
			<div class="join">
				<button
					class="btn join-item btn-sm"
					class:btn-active={uiFilters.is_watched === undefined}
					onclick={() => setBooleanFilter('is_watched', undefined)}
				>
					All
				</button>
				<button
					class="btn join-item btn-sm"
					class:btn-active={uiFilters.is_watched === false}
					onclick={() => setBooleanFilter('is_watched', false)}
				>
					Unwatched
				</button>
				<button
					class="btn join-item btn-sm"
					class:btn-active={uiFilters.is_watched === true}
					onclick={() => setBooleanFilter('is_watched', true)}
				>
					Watched
				</button>
			</div>

			<details class="dropdown dropdown-end">
				<summary class="btn btn-ghost btn-sm">
					Filters
					{#if extendedFilterCount > 0}
						<span class="badge badge-primary badge-sm">{extendedFilterCount}</span>
					{/if}
				</summary>
				<div class="dropdown-content z-20 mt-2 w-80 rounded-box border border-base-300 bg-base-100 p-3 shadow-sm">
					<div class="space-y-2">
						<div class="pb-1 text-xs text-base-content/60">Favorite</div>
						<select
							class="select-bordered select select-sm w-full"
							value={uiFilters.is_favorited === undefined ? '' : String(uiFilters.is_favorited)}
							onchange={(e) =>
								setBooleanFilter(
									'is_favorited',
									(e.currentTarget as HTMLSelectElement).value === ''
										? undefined
										: (e.currentTarget as HTMLSelectElement).value === 'true'
								)
							}
						>
							<option value="">Any favorite</option>
							<option value="true">Favorited</option>
							<option value="false">Not favorited</option>
						</select>

						<div class="pb-1 text-xs text-base-content/60">Length</div>
						<select
							class="select-bordered select select-sm w-full"
							value={uiFilters.is_short === undefined ? '' : String(uiFilters.is_short)}
							onchange={(e) =>
								setBooleanFilter(
									'is_short',
									(e.currentTarget as HTMLSelectElement).value === ''
										? undefined
										: (e.currentTarget as HTMLSelectElement).value === 'true'
								)
							}
						>
							<option value="">Any length</option>
							<option value="true">Shorts only</option>
							<option value="false">No shorts</option>
						</select>

						{#if !isChannelDetailPage}
							<div class="pb-1 text-xs text-base-content/60">Channel</div>
							<select
								class="select-bordered select select-sm w-full"
								value={uiFilters.channel_id ?? ''}
								onchange={(e) =>
									setStringFilter('channel_id', (e.currentTarget as HTMLSelectElement).value)}
							>
								<option value="">All channels</option>
								{#each channels as channel (channel.id)}
									<option value={channel.id}>{channel.title}</option>
								{/each}
							</select>
						{/if}

						<div class="pb-1 text-xs text-base-content/60">Tag</div>
						<select
							class="select-bordered select select-sm w-full"
							value={uiFilters.tag_id ?? ''}
							onchange={(e) => setStringFilter('tag_id', (e.currentTarget as HTMLSelectElement).value)}
						>
							<option value="">All tags</option>
							{#each tags as tag (tag.id)}
								<option value={tag.id}>{tag.name}</option>
							{/each}
						</select>

						<div class="grid grid-cols-2 gap-2">
							<div>
								<div class="pb-1 text-xs text-base-content/60">Published after</div>
								<input
									type="date"
									class="input-bordered input input-sm w-full"
									value={uiFilters.published_after ?? ''}
									onchange={(e) =>
										setStringFilter('published_after', (e.currentTarget as HTMLInputElement).value)}
								/>
							</div>
							<div>
								<div class="pb-1 text-xs text-base-content/60">Published before</div>
								<input
									type="date"
									class="input-bordered input input-sm w-full"
									value={uiFilters.published_before ?? ''}
									onchange={(e) =>
										setStringFilter('published_before', (e.currentTarget as HTMLInputElement).value)}
								/>
							</div>
						</div>

						<div class="grid grid-cols-2 gap-2">
							<div>
								<div class="pb-1 text-xs text-base-content/60">Sort by</div>
								<select
									class="select-bordered select select-sm w-full"
									value={uiFilters.order_by ?? 'published_at'}
									onchange={(e) => setSortFilter('order_by', (e.currentTarget as HTMLSelectElement).value)}
								>
									{#each sortOptions as option}
										<option value={option.value}>{option.label}</option>
									{/each}
								</select>
							</div>
							<div>
								<div class="pb-1 text-xs text-base-content/60">Direction</div>
								<select
									class="select-bordered select select-sm w-full"
									value={uiFilters.order_direction ?? 'desc'}
									onchange={(e) =>
										setSortFilter('order_direction', (e.currentTarget as HTMLSelectElement).value)}
								>
									<option value="desc">Desc</option>
									<option value="asc">Asc</option>
								</select>
							</div>
						</div>
					</div>
					<div class="mt-3 border-t border-base-300 pt-3">
						<button class="btn btn-ghost btn-sm w-full" onclick={clearFilters}>Clear all filters</button>
					</div>
				</div>
			</details>
		</div>
	{:else}
		<div class="flex-1"></div>
	{/if}

	<div class="flex items-center gap-2">
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
