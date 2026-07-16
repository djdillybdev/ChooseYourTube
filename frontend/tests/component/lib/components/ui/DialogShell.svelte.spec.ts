import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeAll, describe, expect, it } from 'vitest';
import DialogShellStub from '../../../stubs/DialogShellStub.svelte';

beforeAll(() => {
	HTMLDialogElement.prototype.showModal = function () {
		this.setAttribute('open', '');
	};
});

describe('DialogShell', () => {
	it('moves focus to the configured control and restores the trigger after cancel', async () => {
		render(DialogShellStub);
		const trigger = screen.getByRole('button', { name: 'Open dialog' });

		trigger.focus();
		await fireEvent.click(trigger);
		const dialog = screen.getByRole('dialog', { name: 'Example dialog' });
		await waitFor(() => expect(screen.getByRole('textbox', { name: 'Name' })).toHaveFocus());

		await fireEvent(dialog, new Event('cancel', { cancelable: true }));

		await waitFor(() => expect(trigger).toHaveFocus());
		expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
	});

	it('closes from the backdrop unless the dialog is busy', async () => {
		render(DialogShellStub);
		const trigger = screen.getByRole('button', { name: 'Open dialog' });
		await fireEvent.click(trigger);

		await fireEvent.click(screen.getByRole('button', { name: 'Close dialog' }));
		expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

		await fireEvent.click(screen.getByRole('checkbox', { name: 'Busy' }));
		await fireEvent.click(trigger);
		await fireEvent.click(screen.getByRole('button', { name: 'Close dialog' }));

		expect(screen.getByRole('dialog', { name: 'Example dialog' })).toBeInTheDocument();
	});
});
