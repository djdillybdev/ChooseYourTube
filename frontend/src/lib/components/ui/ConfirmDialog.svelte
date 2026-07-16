<script lang="ts">
	import DialogShell from './DialogShell.svelte';

	interface Props {
		title: string;
		message: string;
		confirmLabel?: string;
		busy?: boolean;
		error?: string | null;
		onConfirm: () => void | Promise<void>;
		onCancel: () => void;
	}

	let {
		title,
		message,
		confirmLabel = 'Delete',
		busy = false,
		error = null,
		onConfirm,
		onCancel
	}: Props = $props();
	function cancel(event?: Event) {
		event?.preventDefault();
		if (!busy) onCancel();
	}
</script>

<DialogShell
	id="confirmation-dialog"
	titleId="confirmation-title"
	descriptionId="confirmation-message"
	boxClass="max-w-md"
	{busy}
	onClose={cancel}
>
	<h2 id="confirmation-title" class="text-lg font-bold">{title}</h2>
	<p id="confirmation-message" class="mt-2 text-sm text-base-content/80">{message}</p>
	{#if error}<p class="mt-3 text-sm text-error" role="alert">{error}</p>{/if}
	<div class="modal-action">
		<button data-dialog-initial-focus class="btn btn-ghost" disabled={busy} onclick={cancel}>
			Cancel
		</button>
		<button class="btn btn-error" disabled={busy} onclick={() => void onConfirm()}>
			{busy ? 'Working…' : confirmLabel}
		</button>
	</div>
</DialogShell>
