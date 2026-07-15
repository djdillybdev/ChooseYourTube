<script lang="ts">
	import type { LatestSyncSummary, SyncRunOut } from '$lib/types/api';
	import { formatRelativeDate } from '$lib/utils/formatDate';

	interface Props {
		sync: LatestSyncSummary | SyncRunOut | null | undefined;
		compact?: boolean;
	}

	let { sync, compact = false }: Props = $props();
	const statusClass = $derived(
		sync?.status === 'succeeded'
			? 'badge-success'
			: sync?.status === 'partial'
				? 'badge-warning'
				: sync?.status === 'failed'
					? 'badge-error'
					: 'badge-info'
	);
	const successTime = $derived(
		sync && 'last_successful_at' in sync ? sync.last_successful_at : null
	);
</script>

{#if sync}
	<div class="flex flex-wrap items-center gap-2 text-xs">
		<span class="badge badge-sm {statusClass}">{sync.status}</span>
		{#if !compact && successTime}
			<span class="text-base-content/60">Last successful {formatRelativeDate(successTime)}</span>
		{/if}
		{#if sync.error_message && (sync.status === 'failed' || sync.status === 'partial')}
			<span class="text-error">{sync.error_message}</span>
		{/if}
	</div>
{:else if !compact}
	<span class="text-xs text-base-content/90">Not synchronized yet</span>
{/if}
