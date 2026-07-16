export function dismissibleDetails(node: HTMLDetailsElement) {
	function close(restoreFocus = false) {
		if (!node.open) return;

		node.open = false;
		if (restoreFocus) {
			const summary = node.querySelector<HTMLElement>(':scope > summary');
			summary?.focus();
		}
	}

	function handlePointerDown(event: PointerEvent) {
		if (node.open && !event.composedPath().includes(node)) {
			close();
		}
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (!node.open || event.key !== 'Escape') return;

		event.preventDefault();
		close(true);
	}

	document.addEventListener('pointerdown', handlePointerDown);
	document.addEventListener('keydown', handleKeyDown);

	return {
		destroy() {
			document.removeEventListener('pointerdown', handlePointerDown);
			document.removeEventListener('keydown', handleKeyDown);
		}
	};
}
