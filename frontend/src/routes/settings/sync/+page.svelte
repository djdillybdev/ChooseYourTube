<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { api } from '$lib/api';
	import type { PageData } from './$types';
	import type { SyncRunKind } from '$lib/types/api';
	import { formatRelativeDate } from '$lib/utils/formatDate';
	import { SvelteURLSearchParams } from 'svelte/reactivity';
	import StatusBadge from '$lib/components/ui/StatusBadge.svelte';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();
	let retrying = $state<string | null>(null);
	let retryError = $state<string | null>(null);

	function updateFilters(status: string, kind: string) {
		const params = new SvelteURLSearchParams();
		if (status) params.set('status', status);
		if (kind) params.set('kind', kind);
		goto(resolve(`/settings${params.size ? `?${params}` : ''}` as '/settings'));
	}

	function pagePath(page: number) {
		const params = new SvelteURLSearchParams({ page: String(page) });
		if (data.status) params.set('status', data.status);
		if (data.kind) params.set('kind', data.kind);
		return `/settings?${params}` as '/settings';
	}

	async function retry(id: string) {
		retrying = id;
		retryError = null;
		try {
			await api.syncRuns.retry(id);
			await invalidateAll();
		} catch (error) {
			retryError = error instanceof Error ? error.message : 'Could not retry synchronization.';
		} finally {
			retrying = null;
		}
	}

	const kindLabels: Record<SyncRunKind, string> = {
		initial_channel_sync: 'Initial channel sync',
		channel_refresh: 'Channel refresh',
		playlist_sync: 'Playlist sync',
		subscription_import: 'Subscription import',
		demo_maintenance: 'Demo maintenance'
	};
</script>

<svelte:head><title>Sync Activity - Settings - ChooseYourTube</title></svelte:head>

<div class="container mx-auto max-w-6xl p-6">
	<div class="mb-6 flex flex-wrap items-start justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold">Sync Activity</h1>
			<p class="text-base-content/60">Recent channel and playlist synchronization work.</p>
		</div>
		<div class="stats shadow">
			<div class="stat py-3">
				<div class="stat-title">YouTube quota · {data.quota.date}</div>
				<div class="stat-value text-2xl">
					{data.quota.estimated_units_used} / {data.quota.budget}
				</div>
				<div class="stat-desc">Estimated units · {data.quota.call_count} calls</div>
			</div>
		</div>
	</div>

	<div class="mb-4 flex flex-wrap gap-3">
		<select
			class="select-bordered select select-sm"
			aria-label="Filter by status"
			value={data.status ?? ''}
			onchange={(event) => updateFilters(event.currentTarget.value, data.kind ?? '')}
		>
			<option value="">All statuses</option>
			{#each ['queued', 'running', 'succeeded', 'partial', 'failed'] as status (status)}<option
					value={status}>{status}</option
				>{/each}
		</select>
		<select
			class="select-bordered select select-sm"
			aria-label="Filter by kind"
			value={data.kind ?? ''}
			onchange={(event) => updateFilters(data.status ?? '', event.currentTarget.value)}
		>
			<option value="">All types</option>
			{#each Object.entries(kindLabels) as [kind, label] (kind)}<option value={kind}>{label}</option
				>{/each}
		</select>
	</div>

	{#if retryError}<div class="mb-4 alert alert-error" role="alert">{retryError}</div>{/if}
	<div class="sr-only" aria-live="polite">{retrying ? 'Retrying synchronization' : ''}</div>

	{#if data.runs.items.length === 0}
		<div class="rounded-box bg-base-100 p-10 text-center text-base-content/60">
			No synchronization activity matches these filters.
		</div>
	{:else}
		<div class="overflow-x-auto rounded-box bg-base-100 shadow-sm">
			<table class="table">
				<thead
					><tr
						><th>Type</th><th>Status</th><th>Progress</th><th>Started</th><th>Message</th><th
						></th></tr
					></thead
				>
				<tbody
					>{#each data.runs.items as run (run.id)}<tr>
							<td>{kindLabels[run.kind]}</td><td><StatusBadge status={run.status} compact /></td>
							<td
								>{run.items_created} created · {run.items_updated} updated · {run.items_failed} failed</td
							>
							<td>{formatRelativeDate(run.started_at ?? run.queued_at)}</td><td class="max-w-xs"
								>{run.error_message ?? '—'}</td
							>
							<td
								>{#if run.retryable && (run.status === 'failed' || run.status === 'partial')}<button
										class="btn btn-outline btn-xs"
										disabled={retrying === run.id}
										onclick={() => retry(run.id)}
										>{retrying === run.id ? 'Retrying…' : 'Retry'}</button
									>{/if}</td
							>
						</tr>{/each}</tbody
				>
			</table>
		</div>
	{/if}

	{#if data.runs.total > data.pageSize}<div class="join mt-5">
			<a
				class="btn join-item btn-sm"
				class:btn-disabled={data.page <= 1}
				href={resolve(pagePath(Math.max(1, data.page - 1)))}>Previous</a
			><span class="btn join-item btn-sm">Page {data.page}</span><a
				class="btn join-item btn-sm"
				class:btn-disabled={!data.runs.has_more}
				href={resolve(pagePath(data.page + 1))}>Next</a
			>
		</div>{/if}
</div>
