<script lang="ts">
	import type { LatestSyncSummary, SyncRunOut } from '$lib/types/api';
	import { formatRelativeDate } from '$lib/utils/formatDate';
	import StatusBadge from '$lib/components/ui/StatusBadge.svelte';

	interface Props {
		sync: LatestSyncSummary | SyncRunOut | null | undefined;
		compact?: boolean;
	}

	let { sync, compact = false }: Props = $props();
	const successTime = $derived(
		sync && 'last_successful_at' in sync ? sync.last_successful_at : null
	);
</script>

{#if sync}
	<div class="flex flex-wrap items-center gap-2 text-xs">
		<StatusBadge status={sync.status} compact />
		{#if !compact && successTime}
			<span class="text-base-content">Last successful {formatRelativeDate(successTime)}</span>
		{/if}
		{#if sync.error_message && (sync.status === 'failed' || sync.status === 'partial')}
			<span class="text-error">{sync.error_message}</span>
		{/if}
	</div>
{:else if !compact}
	<span class="text-xs text-base-content/90">Not synchronized yet</span>
{/if}
