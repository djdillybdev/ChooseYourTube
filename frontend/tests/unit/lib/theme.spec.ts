import { describe, expect, it } from 'vitest';
import { isThemePreference, resolveTheme, themeName } from '../../../src/lib/theme';

describe('theme utilities', () => {
	it('accepts only supported preferences', () => {
		expect(isThemePreference('latte')).toBe(true);
		expect(isThemePreference('frappe')).toBe(true);
		expect(isThemePreference('macchiato')).toBe(true);
		expect(isThemePreference('mocha')).toBe(true);
		expect(isThemePreference('dracula')).toBe(true);
		expect(isThemePreference('everforest')).toBe(true);
		expect(isThemePreference('everforest-light')).toBe(true);
		expect(isThemePreference('gruvbox')).toBe(true);
		expect(isThemePreference('gruvbox-light')).toBe(true);
		expect(isThemePreference('rose-pine')).toBe(true);
		expect(isThemePreference('rose-pine-moon')).toBe(true);
		expect(isThemePreference('rose-pine-dawn')).toBe(true);
		expect(isThemePreference('system')).toBe(true);
		expect(isThemePreference('catppuccin')).toBe(false);
	});

	it('resolves system preference to the operating system theme', () => {
		expect(resolveTheme('system', false)).toBe('latte');
		expect(resolveTheme('system', true)).toBe('mocha');
		expect(resolveTheme('frappe', false)).toBe('frappe');
		expect(resolveTheme('macchiato', false)).toBe('macchiato');
		expect(resolveTheme('dracula', false)).toBe('dracula');
		expect(resolveTheme('everforest-light', true)).toBe('everforest-light');
		expect(resolveTheme('rose-pine-dawn', false)).toBe('rose-pine-dawn');
	});

	it('maps resolved themes to DaisyUI theme names', () => {
		expect(themeName('latte')).toBe('catppuccin-latte');
		expect(themeName('frappe')).toBe('catppuccin-frappe');
		expect(themeName('macchiato')).toBe('catppuccin-macchiato');
		expect(themeName('mocha')).toBe('catppuccin-mocha');
		expect(themeName('dracula')).toBe('dracula');
		expect(themeName('everforest')).toBe('everforest');
		expect(themeName('everforest-light')).toBe('everforest-light');
		expect(themeName('gruvbox')).toBe('gruvbox');
		expect(themeName('gruvbox-light')).toBe('gruvbox-light');
		expect(themeName('rose-pine')).toBe('rose-pine');
		expect(themeName('rose-pine-moon')).toBe('rose-pine-moon');
		expect(themeName('rose-pine-dawn')).toBe('rose-pine-dawn');
	});
});
