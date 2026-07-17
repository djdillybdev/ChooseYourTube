import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import DurationRangeFilter from '../../../../../src/lib/components/video/DurationRangeFilter.svelte';

describe('DurationRangeFilter', () => {
	it('renders an accessible unbounded range', () => {
		render(DurationRangeFilter, { onchange: vi.fn() });

		expect(screen.getByRole('group', { name: 'Duration' })).toBeInTheDocument();
		expect(screen.getByRole('slider', { name: 'Minimum duration' })).toHaveValue('0');
		expect(screen.getByRole('slider', { name: 'Maximum duration' })).toHaveValue('60');
		expect(screen.getByRole('status')).toHaveTextContent('Any duration');
	});

	it('previews changes on input and commits only on change', async () => {
		const onchange = vi.fn();
		render(DurationRangeFilter, { onchange });
		const minimum = screen.getByRole('slider', { name: 'Minimum duration' });

		await fireEvent.input(minimum, { target: { value: '10' } });
		expect(screen.getByRole('status')).toHaveTextContent('10 min+');
		expect(onchange).not.toHaveBeenCalled();

		await fireEvent.change(minimum, { target: { value: '10' } });
		expect(onchange).toHaveBeenCalledWith({ minMinutes: 10, maxMinutes: undefined });
	});

	it('keeps the bounds ordered and supports one hour plus', async () => {
		const onchange = vi.fn();
		render(DurationRangeFilter, { minMinutes: 30, maxMinutes: 45, onchange });
		const minimum = screen.getByRole('slider', { name: 'Minimum duration' });

		await fireEvent.input(minimum, { target: { value: '60' } });
		expect(screen.getByRole('status')).toHaveTextContent('1hr+');
		await fireEvent.change(minimum, { target: { value: '60' } });

		expect(onchange).toHaveBeenCalledWith({ minMinutes: 60, maxMinutes: undefined });
	});
});
