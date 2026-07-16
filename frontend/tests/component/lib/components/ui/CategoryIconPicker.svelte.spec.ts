import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import CategoryIconPicker from '../../../../../src/lib/components/ui/CategoryIconPicker.svelte';

describe('CategoryIconPicker', () => {
	it('selects an icon and exposes the current selection', async () => {
		const onChange = vi.fn();
		const { rerender } = render(CategoryIconPicker, { value: null, onChange });

		expect(screen.getByRole('radio', { name: 'Default icon' })).toHaveAttribute(
			'aria-checked',
			'true'
		);
		await fireEvent.click(screen.getByRole('radio', { name: 'Gaming' }));
		expect(onChange).toHaveBeenCalledWith('gamepad-2');

		await rerender({ value: 'gamepad-2', onChange });
		expect(screen.getByRole('radio', { name: 'Gaming' })).toHaveAttribute('aria-checked', 'true');
	});

	it('filters the catalog by its readable labels', async () => {
		render(CategoryIconPicker, { value: null, onChange: vi.fn() });

		await fireEvent.input(screen.getByPlaceholderText('Search icons'), {
			target: { value: 'camera' }
		});

		expect(screen.getByRole('radio', { name: 'Camera' })).toBeInTheDocument();
		expect(screen.queryByRole('radio', { name: 'Gaming' })).not.toBeInTheDocument();
	});
});
