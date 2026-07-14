import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import ConfirmDialog from '../../../../../src/lib/components/ui/ConfirmDialog.svelte';

describe('ConfirmDialog', () => {
	it('supports keyboard cancellation and restores focus', async () => {
		HTMLDialogElement.prototype.showModal = function () {
			this.setAttribute('open', '');
		};
		const trigger = document.createElement('button');
		document.body.append(trigger);
		trigger.focus();
		const onCancel = vi.fn();
		const { unmount } = render(ConfirmDialog, {
			title: 'Delete item?',
			message: 'This cannot be undone.',
			onConfirm: vi.fn(),
			onCancel
		});

		const dialog = screen.getByRole('dialog');
		await fireEvent(dialog, new Event('cancel', { cancelable: true }));
		expect(onCancel).toHaveBeenCalledOnce();
		unmount();
		expect(document.activeElement).toBe(trigger);
		trigger.remove();
	});
});
