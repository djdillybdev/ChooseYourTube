<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import type { ChannelOut, TagOut } from '$lib/types/api';
	import { parseVideoFilterQuery } from '$lib/utils/videoFilterQuery';
	import { dismissibleDetails } from '$lib/actions/dismissibleDetails';
	import DurationRangeFilter from './DurationRangeFilter.svelte';

	interface Props {
		channels?: ChannelOut[];
		tags?: TagOut[];
		currentPath: string;
	}

	let { channels = [], tags = [], currentPath }: Props = $props();

	const isChannelDetailPage = $derived(currentPath.startsWith('/channels/'));
	const { uiFilters } = $derived(
		parseVideoFilterQuery(page.url, {
			defaultWatched: currentPath === '/inbox' ? false : undefined
		})
	);
	const filterCount = $derived(
		[
			uiFilters.channel_id,
			uiFilters.tag_id,
			uiFilters.published_after,
			uiFilters.published_before
		].filter((value) => value !== undefined && value !== '').length +
			(uiFilters.min_duration_minutes !== undefined || uiFilters.max_duration_minutes !== undefined
				? 1
				: 0) +
			(uiFilters.is_short !== false ? 1 : 0) +
			(uiFilters.order_by && uiFilters.order_by !== 'published_at' ? 1 : 0) +
			(uiFilters.order_direction && uiFilters.order_direction !== 'desc' ? 1 : 0)
	);

	const sortOptions = [
		{ value: 'published_at', label: 'Published date' },
		{ value: 'title', label: 'Title' },
		{ value: 'created_at', label: 'Date added' },
		{ value: 'duration_seconds', label: 'Duration' },
		{ value: 'relevance', label: 'Relevance' }
	] as const;

	function updateQuery(mutator: (params: URLSearchParams) => void) {
		const url = new URL(page.url);
		mutator(url.searchParams);
		url.searchParams.set('page', '1');
		goto(resolve(`${url.pathname}${url.search}` as '/inbox'), {
			keepFocus: true,
			noScroll: true
		});
	}

	function setBooleanFilter(key: 'is_watched' | 'is_short', value: boolean | undefined) {
		updateQuery((params) => params.set(key, value === undefined ? 'all' : String(value)));
	}

	function setStringFilter(
		key: 'channel_id' | 'tag_id' | 'published_after' | 'published_before',
		value: string
	) {
		updateQuery((params) => {
			if (value) params.set(key, value);
			else params.delete(key);
		});
	}

	function setSortFilter(key: 'order_by' | 'order_direction', value: string) {
		updateQuery((params) => {
			if (value) params.set(key, value);
			else params.delete(key);
		});
	}

	function setDurationFilter({
		minMinutes,
		maxMinutes
	}: {
		minMinutes: number | undefined;
		maxMinutes: number | undefined;
	}) {
		updateQuery((params) => {
			if (minMinutes === undefined) params.delete('min_duration_minutes');
			else params.set('min_duration_minutes', String(minMinutes));

			if (maxMinutes === undefined) params.delete('max_duration_minutes');
			else params.set('max_duration_minutes', String(maxMinutes));
		});
	}

	function resetFilters() {
		updateQuery((params) => {
			for (const key of [
				'is_watched',
				'is_short',
				'channel_id',
				'tag_id',
				'published_after',
				'published_before',
				'min_duration_minutes',
				'max_duration_minutes',
				'order_by',
				'order_direction'
			]) {
				params.delete(key);
			}
		});
	}
</script>

<div class="flex min-w-0 items-center justify-center gap-2">
	<fieldset class="join hidden sm:flex">
		<legend class="sr-only">Watched state</legend>
		<button
			type="button"
			class="btn join-item btn-sm"
			class:btn-active={uiFilters.is_watched === undefined}
			aria-pressed={uiFilters.is_watched === undefined}
			onclick={() => setBooleanFilter('is_watched', undefined)}>All</button
		>
		<button
			type="button"
			class="btn join-item btn-sm"
			class:btn-active={uiFilters.is_watched === false}
			aria-pressed={uiFilters.is_watched === false}
			onclick={() => setBooleanFilter('is_watched', false)}>Unwatched</button
		>
		<button
			type="button"
			class="btn join-item btn-sm"
			class:btn-active={uiFilters.is_watched === true}
			aria-pressed={uiFilters.is_watched === true}
			onclick={() => setBooleanFilter('is_watched', true)}>Watched</button
		>
	</fieldset>

	<details class="dropdown dropdown-end" use:dismissibleDetails>
		<summary class="btn btn-ghost btn-sm">
			Filters
			{#if filterCount > 0}
				<span class="badge badge-sm badge-primary" aria-label={`${filterCount} active filters`}>
					{filterCount}
				</span>
			{/if}
		</summary>
		<div
			class="filter-panel dropdown-content fixed top-16 right-2 left-2 z-20 mt-2 max-h-[calc(100dvh-5rem)] overflow-y-auto rounded-box border border-base-300 bg-base-100 p-3 text-base-content shadow-sm sm:absolute sm:top-full sm:right-0 sm:left-auto sm:w-80"
		>
			<div class="space-y-3">
				<div class="sm:hidden">
					<label class="mb-1 block text-xs font-medium text-base-content" for="watched-filter">
						Watched state
					</label>
					<select
						id="watched-filter"
						class="select-bordered select w-full select-sm text-base-content"
						value={uiFilters.is_watched === undefined ? 'all' : String(uiFilters.is_watched)}
						onchange={(event) => {
							const value = event.currentTarget.value;
							setBooleanFilter('is_watched', value === 'all' ? undefined : value === 'true');
						}}
					>
						<option value="all">All videos</option>
						<option value="false">Unwatched</option>
						<option value="true">Watched</option>
					</select>
				</div>

				<DurationRangeFilter
					minMinutes={uiFilters.min_duration_minutes}
					maxMinutes={uiFilters.max_duration_minutes}
					onchange={setDurationFilter}
				/>

				<div>
					<label class="mb-1 block text-xs font-medium text-base-content" for="shorts-filter">
						Shorts
					</label>
					<select
						id="shorts-filter"
						class="select-bordered select w-full select-sm text-base-content"
						value={uiFilters.is_short === undefined ? 'all' : String(uiFilters.is_short)}
						onchange={(event) => {
							const value = event.currentTarget.value;
							setBooleanFilter('is_short', value === 'all' ? undefined : value === 'true');
						}}
					>
						<option value="false">Standard videos</option>
						<option value="all">All lengths</option>
						<option value="true">Shorts only</option>
					</select>
				</div>

				{#if !isChannelDetailPage}
					<div>
						<label class="mb-1 block text-xs font-medium text-base-content" for="channel-filter">
							Channel
						</label>
						<select
							id="channel-filter"
							class="select-bordered select w-full select-sm text-base-content"
							value={uiFilters.channel_id ?? ''}
							onchange={(event) => setStringFilter('channel_id', event.currentTarget.value)}
						>
							<option value="">All channels</option>
							{#each channels as channel (channel.id)}
								<option value={channel.id}>{channel.title}</option>
							{/each}
						</select>
					</div>
				{/if}

				<div>
					<label class="mb-1 block text-xs font-medium text-base-content" for="tag-filter">
						Tag
					</label>
					<select
						id="tag-filter"
						class="select-bordered select w-full select-sm text-base-content"
						value={uiFilters.tag_id ?? ''}
						onchange={(event) => setStringFilter('tag_id', event.currentTarget.value)}
					>
						<option value="">All tags</option>
						{#each tags as tag (tag.id)}
							<option value={tag.id}>{tag.name}</option>
						{/each}
					</select>
				</div>

				<div class="grid grid-cols-1 gap-2 min-[360px]:grid-cols-2">
					<div>
						<label
							class="mb-1 block text-xs font-medium text-base-content"
							for="published-after-filter">Published after</label
						>
						<input
							id="published-after-filter"
							type="date"
							class="input-bordered input input-sm w-full text-base-content"
							value={uiFilters.published_after ?? ''}
							onchange={(event) => setStringFilter('published_after', event.currentTarget.value)}
						/>
					</div>
					<div>
						<label
							class="mb-1 block text-xs font-medium text-base-content"
							for="published-before-filter">Published before</label
						>
						<input
							id="published-before-filter"
							type="date"
							class="input-bordered input input-sm w-full text-base-content"
							value={uiFilters.published_before ?? ''}
							onchange={(event) => setStringFilter('published_before', event.currentTarget.value)}
						/>
					</div>
				</div>

				<div class="grid grid-cols-1 gap-2 min-[360px]:grid-cols-2">
					<div>
						<label class="mb-1 block text-xs font-medium text-base-content" for="sort-filter">
							Sort by
						</label>
						<select
							id="sort-filter"
							class="select-bordered select w-full select-sm text-base-content"
							value={uiFilters.order_by ?? 'published_at'}
							onchange={(event) => setSortFilter('order_by', event.currentTarget.value)}
						>
							{#each sortOptions as option (option.value)}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium text-base-content" for="direction-filter"
							>Direction</label
						>
						<select
							id="direction-filter"
							class="select-bordered select w-full select-sm text-base-content"
							value={uiFilters.order_direction ?? 'desc'}
							onchange={(event) => setSortFilter('order_direction', event.currentTarget.value)}
						>
							<option value="desc">Newest first</option>
							<option value="asc">Oldest first</option>
						</select>
					</div>
				</div>
			</div>

			<div class="mt-3 border-t border-base-300 pt-3">
				<button type="button" class="btn w-full btn-ghost btn-sm" onclick={resetFilters}>
					Reset filters
				</button>
			</div>
		</div>
	</details>
</div>

<style>
	details[open] > .filter-panel {
		opacity: 1 !important;
		transform: none;
		transition: none !important;
	}

	.filter-panel label,
	.filter-panel input[type='date'],
	.filter-panel input[type='date']::-webkit-datetime-edit {
		color: #3b3e55 !important;
		opacity: 1;
	}
</style>
