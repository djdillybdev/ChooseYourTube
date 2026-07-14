<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { api } from '$lib/api';
	import { pollSyncRun } from '$lib/utils/syncPolling';
	import type { PageData } from './$types';
	import type { SubscriptionCandidateState, SyncRunOut } from '$lib/types/api';
	import { SvelteSet, SvelteURLSearchParams } from 'svelte/reactivity';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();
	let folderId = $state('');
	const selectedTags = new SvelteSet<string>();
	let initialized = false;
	$effect(() => {
		if (!initialized) {
			folderId = data.detail.import.destination_folder_id ?? '';
			for (const tagId of data.detail.import.destination_tag_ids) selectedTags.add(tagId);
			initialized = true;
		}
	});
	let saving = $state<string | null>(null);
	let committing = $state(false);
	let run = $state<SyncRunOut | null>(null);
	let error = $state<string | null>(null);
	let cancelled = false;
	$effect(() => () => {
		cancelled = true;
	});

	const tabs: { state: SubscriptionCandidateState; label: string; count: () => number }[] = [
		{ state: 'new', label: 'New', count: () => data.detail.import.new_count },
		{ state: 'selected', label: 'Selected', count: () => data.detail.import.selected_count },
		{ state: 'existing', label: 'Existing', count: () => data.detail.import.existing_count },
		{ state: 'invalid', label: 'Invalid', count: () => data.detail.import.invalid_count },
		{ state: 'imported', label: 'Imported', count: () => data.detail.import.imported_count },
		{ state: 'failed', label: 'Failed', count: () => data.detail.import.failed_count }
	];

	function path(state: SubscriptionCandidateState, page = 1) {
		const params = new SvelteURLSearchParams({ state });
		if (data.search) params.set('search', data.search);
		if (page > 1) params.set('page', String(page));
		return `/settings/imports/${data.detail.import.id}?${params}`;
	}

	async function selectCandidate(id: string, selected: boolean) {
		saving = id;
		error = null;
		try {
			await api.imports.updateSelection(data.detail.import.id, {
				candidate_ids: [id],
				selected
			});
			await invalidateAll();
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Selection could not be saved.';
		} finally {
			saving = null;
		}
	}

	function toggleTag(id: string) {
		if (selectedTags.has(id)) selectedTags.delete(id);
		else selectedTags.add(id);
	}

	async function commit(retryFailed = false) {
		committing = true;
		error = null;
		try {
			run = await api.imports.commit(data.detail.import.id, {
				folder_id: folderId || null,
				tag_ids: [...selectedTags],
				selected_candidate_ids: retryFailed ? undefined : null
			});
			await pollSyncRun(
				run.id,
				(id) => api.syncRuns.get(id),
				(value) => (run = value),
				() => cancelled
			);
			await invalidateAll();
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'The import could not be started.';
		} finally {
			committing = false;
		}
	}
</script>

<svelte:head><title>Review Subscription Import - ChooseYourTube</title></svelte:head>

<div class="container mx-auto max-w-6xl p-6">
	<div class="mb-5 flex flex-wrap items-start justify-between gap-4">
		<div>
			<h2 class="text-2xl font-bold">Review subscriptions</h2>
			<p class="text-base-content/60">{data.detail.import.candidate_count} rows discovered</p>
		</div>
		<span class="badge badge-lg">{data.detail.import.status}</span>
	</div>

	{#if error}<div class="mb-4 alert alert-error" role="alert">{error}</div>{/if}
	{#if data.detail.import.error_message}
		<div class="mb-4 alert alert-warning" role="alert">{data.detail.import.error_message}</div>
	{/if}
	<div class="sr-only" aria-live="polite">
		{saving
			? 'Saving selection'
			: committing
				? 'Import in progress'
				: run
					? `Import ${run.status}`
					: ''}
	</div>

	<div role="tablist" class="tabs-border mb-4 tabs overflow-x-auto">
		{#each tabs as tab (tab.state)}
			<a
				role="tab"
				class="tab whitespace-nowrap"
				class:tab-active={data.state === tab.state}
				href={resolve(path(tab.state) as '/settings')}>{tab.label} ({tab.count()})</a
			>
		{/each}
	</div>

	<form class="mb-4 flex gap-2" method="GET">
		<input type="hidden" name="state" value={data.state} />
		<label class="sr-only" for="candidate-search">Search candidates</label>
		<input
			id="candidate-search"
			name="search"
			value={data.search ?? ''}
			placeholder="Search title or channel ID"
			class="input-bordered input w-full max-w-md"
		/>
		<button class="btn btn-outline" type="submit">Search</button>
	</form>

	<div class="overflow-x-auto rounded-box bg-base-100 shadow-sm">
		<table class="table">
			<thead
				><tr><th class="w-16">Select</th><th>Channel</th><th>Channel ID</th><th>Note</th></tr
				></thead
			>
			<tbody>
				{#each data.detail.candidates.items as candidate (candidate.id)}
					<tr>
						<td>
							{#if candidate.state === 'new' || candidate.state === 'selected'}
								<input
									type="checkbox"
									class="checkbox checkbox-sm"
									aria-label={`Select ${candidate.channel_title ?? candidate.channel_id}`}
									checked={candidate.state === 'selected'}
									disabled={saving === candidate.id}
									onchange={(event) => selectCandidate(candidate.id, event.currentTarget.checked)}
								/>
							{:else}—{/if}
						</td>
						<td>{candidate.channel_title ?? 'Unknown channel'}</td>
						<td class="font-mono text-xs">{candidate.channel_id ?? '—'}</td>
						<td class="text-sm text-base-content/60">{candidate.message ?? '—'}</td>
					</tr>
				{:else}
					<tr
						><td colspan="4" class="py-10 text-center text-base-content/60"
							>No matching candidates.</td
						></tr
					>
				{/each}
			</tbody>
		</table>
	</div>

	{#if data.detail.candidates.total > data.pageSize}
		<div class="join mt-4">
			<a
				class="btn join-item btn-sm"
				class:btn-disabled={data.page <= 1}
				href={resolve(path(data.state, data.page - 1) as '/settings')}>Previous</a
			>
			<span class="btn join-item btn-sm">Page {data.page}</span>
			<a
				class="btn join-item btn-sm"
				class:btn-disabled={!data.detail.candidates.has_more}
				href={resolve(path(data.state, data.page + 1) as '/settings')}>Next</a
			>
		</div>
	{/if}

	{#if data.detail.import.status === 'ready'}
		<section class="mt-6 rounded-box bg-base-100 p-5 shadow-sm">
			<h3 class="mb-4 font-semibold">Organize new channels</h3>
			<div class="grid gap-4 md:grid-cols-2">
				<label class="form-control">
					<span class="label-text mb-1">Folder (optional)</span>
					<select class="select-bordered select" bind:value={folderId}>
						<option value="">No folder</option>
						{#each data.folders as folder (folder.id)}<option value={folder.id}
								>{folder.name}</option
							>{/each}
					</select>
				</label>
				<fieldset>
					<legend class="label-text mb-2">Tags (optional)</legend>
					<div class="flex flex-wrap gap-2">
						{#each data.tags as tag (tag.id)}
							<label class="label cursor-pointer gap-2 rounded border border-base-300 px-3 py-2">
								<input
									type="checkbox"
									class="checkbox checkbox-xs"
									checked={selectedTags.has(tag.id)}
									onchange={() => toggleTag(tag.id)}
								/>
								<span>{tag.name}</span>
							</label>
						{/each}
					</div>
				</fieldset>
			</div>
			<button
				class="btn mt-5 btn-primary"
				disabled={committing || data.detail.import.selected_count === 0}
				onclick={() => commit(false)}
			>
				{committing ? 'Importing…' : `Import ${data.detail.import.selected_count} channels`}
			</button>
		</section>
	{:else if (data.detail.import.status === 'partial' || data.detail.import.status === 'failed') && data.detail.import.failed_count > 0}
		<button class="btn mt-5 btn-primary" disabled={committing} onclick={() => commit(true)}>
			{committing ? 'Retrying…' : `Retry ${data.detail.import.failed_count} failed`}
		</button>
	{/if}
</div>
