import { fireEvent, render, screen } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import SearchBar from '../../../../../src/lib/components/ui/SearchBar.svelte';

const { gotoMock } = vi.hoisted(() => ({ gotoMock: vi.fn() }));

vi.mock('$app/navigation', () => ({
	goto: gotoMock
}));

describe('SearchBar', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		gotoMock.mockReset();
		history.replaceState({}, '', '/inbox?page=3&pageSize=24');
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it('updates q query param with debounce and resets page to 1', async () => {
		render(SearchBar, { basePath: '/inbox' });

		const input = screen.getByPlaceholderText('Search videos...');
		await fireEvent.input(input, { target: { value: 'svelte' } });

		expect(gotoMock).not.toHaveBeenCalled();
		vi.advanceTimersByTime(300);

		expect(gotoMock).toHaveBeenCalledWith('/inbox?page=1&pageSize=24&q=svelte', {
			keepFocus: true
		});
	});

	it('clears query param when clear button is clicked', async () => {
		render(SearchBar, { basePath: '/inbox', initialValue: 'initial' });

		await fireEvent.click(screen.getByRole('button', { name: /clear search/i }));

		expect(gotoMock).toHaveBeenCalledWith('/inbox?page=1&pageSize=24', {
			keepFocus: true
		});
	});
});
