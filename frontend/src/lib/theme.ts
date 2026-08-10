export type ThemeFlavor =
	| 'latte'
	| 'frappe'
	| 'macchiato'
	| 'mocha'
	| 'dracula'
	| 'everforest'
	| 'everforest-light'
	| 'gruvbox'
	| 'gruvbox-light'
	| 'rose-pine'
	| 'rose-pine-moon'
	| 'rose-pine-dawn';
export type ThemePreference = ThemeFlavor | 'system';
export type ResolvedTheme = ThemeFlavor;

export const defaultThemePreference: ThemePreference = 'latte';

export const themeOptions: Array<{
	value: ThemePreference;
	label: string;
	description: string;
	preview: string[];
}> = [
	{
		value: 'latte',
		label: 'Latte',
		description: 'The lightest Catppuccin theme with a bright, airy interface.',
		preview: ['#eff1f5', '#8839ef', '#209fb5']
	},
	{
		value: 'frappe',
		label: 'Frappé',
		description: 'A muted, subdued theme with a softer contrast.',
		preview: ['#303446', '#ca9ee6', '#85c1dc']
	},
	{
		value: 'macchiato',
		label: 'Macchiato',
		description: 'A medium-contrast theme with gentle, soothing colors.',
		preview: ['#24273a', '#c6a0f6', '#7dc4e4']
	},
	{
		value: 'mocha',
		label: 'Mocha',
		description: 'The darkest Catppuccin theme with rich, cozy accents.',
		preview: ['#1e1e2e', '#cba6f7', '#89dceb']
	},
	{
		value: 'dracula',
		label: 'Dracula',
		description: 'A dark theme with vivid purple, pink, and cyan accents.',
		preview: ['#282a36', '#bd93f9', '#8be9fd']
	},
	{
		value: 'everforest',
		label: 'Everforest',
		description: 'A warm, soft green-based theme designed for comfortable viewing.',
		preview: ['#2d353b', '#a7c080', '#7fbbb3']
	},
	{
		value: 'everforest-light',
		label: 'Everforest Light',
		description: 'Everforest’s warm, soft light palette with green-based accents.',
		preview: ['#fdf6e3', '#8da101', '#3a94c5']
	},
	{
		value: 'gruvbox',
		label: 'Gruvbox',
		description: 'A retro groove theme with warm pastel colors.',
		preview: ['#282828', '#d79921', '#458588']
	},
	{
		value: 'gruvbox-light',
		label: 'Gruvbox Light',
		description: 'Gruvbox’s bright retro palette with warm pastel colors.',
		preview: ['#fbf1c7', '#b57614', '#076678']
	},
	{
		value: 'rose-pine',
		label: 'Rosé Pine',
		description: 'A cozy dark theme built around muted rose and pine accents.',
		preview: ['#191724', '#c4a7e7', '#31748f']
	},
	{
		value: 'rose-pine-moon',
		label: 'Rosé Pine Moon',
		description: 'A softer, medium-contrast Rosé Pine dark variant.',
		preview: ['#232136', '#c4a7e7', '#3e8fb0']
	},
	{
		value: 'rose-pine-dawn',
		label: 'Rosé Pine Dawn',
		description: 'The light Rosé Pine variant with warm, gentle colors.',
		preview: ['#faf4ed', '#907aa9', '#286983']
	},
	{
		value: 'system',
		label: 'System',
		description: 'Use Latte in light mode and Mocha in dark mode.',
		preview: ['#eff1f5', '#1e1e2e', '#cba6f7']
	}
];

export function isThemePreference(value: unknown): value is ThemePreference {
	return (
		value === 'latte' ||
		value === 'frappe' ||
		value === 'macchiato' ||
		value === 'mocha' ||
		value === 'dracula' ||
		value === 'everforest' ||
		value === 'gruvbox' ||
		value === 'everforest-light' ||
		value === 'gruvbox-light' ||
		value === 'rose-pine' ||
		value === 'rose-pine-moon' ||
		value === 'rose-pine-dawn' ||
		value === 'system'
	);
}

export function normalizeThemePreference(value: unknown): ThemePreference {
	if (value === 'light') return 'latte';
	if (value === 'dark') return 'mocha';
	return isThemePreference(value) ? value : defaultThemePreference;
}

export function resolveTheme(preference: ThemePreference, prefersDark: boolean): ResolvedTheme {
	if (preference === 'system') return prefersDark ? 'mocha' : 'latte';
	return preference;
}

export function themeName(theme: ResolvedTheme): string {
	return ['latte', 'frappe', 'macchiato', 'mocha'].includes(theme) ? `catppuccin-${theme}` : theme;
}

function isLightTheme(theme: ResolvedTheme): boolean {
	return (
		theme === 'latte' ||
		theme === 'everforest-light' ||
		theme === 'gruvbox-light' ||
		theme === 'rose-pine-dawn'
	);
}

export function applyTheme(preference: ThemePreference): ResolvedTheme {
	const prefersDark =
		typeof window !== 'undefined' &&
		typeof window.matchMedia === 'function' &&
		window.matchMedia('(prefers-color-scheme: dark)').matches;
	const resolved = resolveTheme(preference, prefersDark);

	if (typeof document !== 'undefined') {
		document.documentElement.dataset.theme = themeName(resolved);
		document.documentElement.style.colorScheme = isLightTheme(resolved) ? 'light' : 'dark';
	}

	return resolved;
}
