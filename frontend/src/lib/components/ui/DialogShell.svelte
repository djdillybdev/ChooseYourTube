<script lang="ts">
	import { onMount, tick, type Snippet } from 'svelte';

	interface Props {
		id: string;
		titleId: string;
		descriptionId?: string;
		busy?: boolean;
		boxClass?: string;
		onClose: () => void;
		children: Snippet;
	}

	let {
		id,
		titleId,
		descriptionId,
		busy = false,
		boxClass = '',
		onClose,
		children
	}: Props = $props();

	let dialog: HTMLDialogElement;
	let trigger: HTMLElement | null = null;

	onMount(() => {
		trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null;
		dialog.showModal();
		void tick().then(() => {
			const initial = dialog.querySelector<HTMLElement>('[data-dialog-initial-focus]');
			const fallback = dialog.querySelector<HTMLElement>(
				'input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), a[href]'
			);
			(initial ?? fallback)?.focus();
		});

		return () => {
			if (trigger?.isConnected) {
				trigger.focus();
				return;
			}
			document.querySelector<HTMLElement>('#main-content, main, h1')?.focus();
		};
	});

	function requestClose(event?: Event) {
		event?.preventDefault();
		if (!busy) onClose();
	}
</script>

<dialog
	bind:this={dialog}
	{id}
	class="modal"
	aria-labelledby={titleId}
	aria-describedby={descriptionId}
	aria-busy={busy}
	oncancel={requestClose}
>
	<div class={`modal-box max-h-[calc(100dvh-2rem)] overflow-y-auto ${boxClass}`}>
		{@render children()}
	</div>
	<form method="dialog" class="modal-backdrop">
		<button type="button" onclick={requestClose} aria-label="Close dialog">close</button>
	</form>
</dialog>
