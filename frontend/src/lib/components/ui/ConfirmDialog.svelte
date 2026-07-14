<script lang="ts">
	import { onMount } from 'svelte';

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
	let dialog: HTMLDialogElement;
	let cancelButton: HTMLButtonElement;

	onMount(() => {
		const trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null;
		dialog.showModal();
		cancelButton.focus();
		return () => trigger?.focus();
	});

	function cancel(event?: Event) {
		event?.preventDefault();
		if (!busy) onCancel();
	}
</script>

<dialog bind:this={dialog} class="modal" oncancel={cancel} aria-labelledby="confirm-title">
	<div class="modal-box max-w-md">
		<h2 id="confirm-title" class="text-lg font-bold">{title}</h2>
		<p class="mt-2 text-sm text-base-content/70">{message}</p>
		{#if error}<p class="mt-3 text-sm text-error" role="alert">{error}</p>{/if}
		<div class="modal-action">
			<button bind:this={cancelButton} class="btn btn-ghost" disabled={busy} onclick={cancel}>
				Cancel
			</button>
			<button class="btn btn-error" disabled={busy} onclick={() => void onConfirm()}>
				{busy ? 'Working…' : confirmLabel}
			</button>
		</div>
	</div>
</dialog>
