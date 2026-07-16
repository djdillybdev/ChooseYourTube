import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import DismissibleDetailsStub from '../../stubs/DismissibleDetailsStub.svelte';

describe('dismissibleDetails', () => {
	it('closes an open details element after an outside pointer interaction', async () => {
		render(DismissibleDetailsStub);
		const summary = screen.getByText('Open menu');
		const details = summary.closest('details');
		expect(details).not.toBeNull();
		details!.open = true;

		await fireEvent.pointerDown(screen.getByRole('button', { name: 'Outside control' }));

		expect(details).not.toHaveAttribute('open');
	});

	it('keeps the details element open for interactions inside it', async () => {
		render(DismissibleDetailsStub);
		const details = screen.getByText('Open menu').closest('details');
		expect(details).not.toBeNull();
		details!.open = true;

		await fireEvent.pointerDown(screen.getByRole('textbox', { name: 'Menu field' }));

		expect(details).toHaveAttribute('open');
	});

	it('closes on Escape and restores focus to the summary', async () => {
		render(DismissibleDetailsStub);
		const summary = screen.getByText('Open menu');
		const details = summary.closest('details');
		expect(details).not.toBeNull();
		details!.open = true;
		screen.getByRole('textbox', { name: 'Menu field' }).focus();

		await fireEvent.keyDown(document, { key: 'Escape' });

		expect(details).not.toHaveAttribute('open');
		expect(summary).toHaveFocus();
	});
});
