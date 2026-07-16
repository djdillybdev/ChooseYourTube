<script lang="ts">
	import DialogShell from '../../../src/lib/components/ui/DialogShell.svelte';

	let open = $state(false);
	let busy = $state(false);
</script>

<button type="button" onclick={() => (open = true)}>Open dialog</button>
<label>
	Busy
	<input type="checkbox" bind:checked={busy} />
</label>

{#if open}
	<DialogShell
		id="test-dialog"
		titleId="test-dialog-title"
		descriptionId="test-dialog-description"
		{busy}
		onClose={() => (open = false)}
	>
		<h2 id="test-dialog-title">Example dialog</h2>
		<p id="test-dialog-description">Example description</p>
		<label>
			Name
			<input data-dialog-initial-focus />
		</label>
		<button type="button">Save</button>
	</DialogShell>
{/if}
