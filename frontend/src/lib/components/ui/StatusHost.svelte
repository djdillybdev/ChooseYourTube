<script lang="ts">
	import { actionStatus } from '$lib/stores/actionStatus.svelte';
</script>

<div
	class="pointer-events-none fixed right-3 bottom-3 z-[70] max-w-sm"
	aria-live="polite"
	aria-atomic="true"
>
	{#if actionStatus.current}
		<div
			class="pointer-events-auto alert border border-base-300 bg-base-100 shadow-lg"
			role="status"
		>
			<span>{actionStatus.current.message}</span>
			<button
				type="button"
				class="btn btn-square btn-ghost btn-sm"
				onclick={() => actionStatus.clear()}
				aria-label="Dismiss notification">×</button
			>
		</div>
	{/if}
</div>
