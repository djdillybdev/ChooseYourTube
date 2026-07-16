import { browser } from '$app/environment';
import { SvelteSet } from 'svelte/reactivity';

const STORAGE_KEY = 'chooseyourtube:expandedCategories';

class CategoryExpansionState {
	expanded = $state(new SvelteSet<string>());

	constructor() {
		if (!browser) return;
		try {
			const stored =
				typeof localStorage.getItem === 'function' ? localStorage.getItem(STORAGE_KEY) : null;
			if (stored) this.expanded = new SvelteSet(JSON.parse(stored) as string[]);
		} catch {
			this.expanded = new SvelteSet();
		}
	}

	isExpanded(id: string): boolean {
		return this.expanded.has(id);
	}

	toggle(id: string): void {
		if (this.expanded.has(id)) this.expanded.delete(id);
		else this.expanded.add(id);
		if (browser && typeof localStorage.setItem === 'function') {
			localStorage.setItem(STORAGE_KEY, JSON.stringify([...this.expanded]));
		}
	}
}

export const categoryExpansion = new CategoryExpansionState();
