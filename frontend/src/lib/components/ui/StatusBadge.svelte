<script lang="ts">
	import type { SyncRunStatus } from '$lib/types/api';

	interface Props {
		status: SyncRunStatus;
		compact?: boolean;
	}

	let { status, compact = false }: Props = $props();
	const label = $derived(
		status === 'queued'
			? 'Sync queued'
			: status === 'running'
				? 'Sync in progress'
				: status === 'succeeded'
					? 'Sync succeeded'
					: status === 'partial'
						? 'Sync partially completed'
						: 'Sync failed'
	);
	const statusClass = $derived(
		status === 'succeeded'
			? 'badge-success'
			: status === 'partial'
				? 'badge-warning'
				: status === 'failed'
					? 'badge-error'
					: 'badge-info'
	);
</script>

<span class="badge {compact ? 'badge-sm' : ''} {statusClass}">{label}</span>
