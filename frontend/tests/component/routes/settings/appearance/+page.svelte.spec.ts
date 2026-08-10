import { fireEvent, render, screen } from '@testing-library/svelte';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import AppearancePage from '../../../../../src/routes/settings/appearance/+page.svelte';
import { setTheme, uiState } from '../../../../../src/lib/stores/uiState.svelte';

describe('Appearance settings', () => {
	beforeEach(() => {
		const values = new Map<string, string>();
		vi.stubGlobal('localStorage', {
			getItem: (key: string) => values.get(key) ?? null,
			setItem: (key: string, value: string) => values.set(key, value),
			removeItem: (key: string) => values.delete(key),
			clear: () => values.clear()
		});
		setTheme('latte');
		vi.stubGlobal('matchMedia', () => ({ matches: false }));
	});

	it('offers light, dark, and system theme choices', () => {
		render(AppearancePage);

		expect(screen.getByRole('radio', { name: /^Latte / })).toBeChecked();
		expect(screen.getByRole('radio', { name: /^Frappé / })).toBeInTheDocument();
		expect(screen.getByRole('radio', { name: /^Macchiato / })).toBeInTheDocument();
		expect(screen.getByRole('radio', { name: /^Mocha / })).toBeInTheDocument();
		expect(screen.getByRole('radio', { name: /^Dracula / })).toBeInTheDocument();
		expect(screen.getByDisplayValue('everforest')).toBeInTheDocument();
		expect(screen.getByDisplayValue('everforest-light')).toBeInTheDocument();
		expect(screen.getByDisplayValue('gruvbox')).toBeInTheDocument();
		expect(screen.getByDisplayValue('gruvbox-light')).toBeInTheDocument();
		expect(screen.getByDisplayValue('rose-pine')).toBeInTheDocument();
		expect(screen.getByDisplayValue('rose-pine-moon')).toBeInTheDocument();
		expect(screen.getByDisplayValue('rose-pine-dawn')).toBeInTheDocument();
		expect(screen.getByRole('radio', { name: /^System / })).toBeInTheDocument();
	});

	it('changes and persists the selected theme', async () => {
		render(AppearancePage);

		await fireEvent.click(screen.getByRole('radio', { name: /^Macchiato / }));

		expect(uiState.current.theme).toBe('macchiato');
		expect(document.documentElement).toHaveAttribute('data-theme', 'catppuccin-macchiato');
	});
});
