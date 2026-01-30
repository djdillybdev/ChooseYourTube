/**
 * Manages folder expansion state in the sidebar.
 * Persists which folders are expanded/collapsed to localStorage.
 */

import { SvelteSet } from 'svelte/reactivity';

const STORAGE_KEY = 'chooseyourtube:expandedFolders';

class FolderExpansionState {
	private expanded = $state(new SvelteSet<number>());

	constructor() {
		// Load expansion state from localStorage on initialization
		if (typeof window !== 'undefined') {
			const stored = localStorage.getItem(STORAGE_KEY);
			if (stored) {
				try {
					const ids = JSON.parse(stored) as number[];
					this.expanded = new SvelteSet(ids);
				} catch (error) {
					console.error('Failed to parse folder expansion state:', error);
					this.expanded = new SvelteSet();
				}
			}
		}
	}

	/**
	 * Toggle expansion state for a folder.
	 * If expanded, collapse it. If collapsed, expand it.
	 */
	toggle(folderId: number) {
		// SvelteSet is reactive, so direct mutations trigger updates
		if (this.expanded.has(folderId)) {
			this.expanded.delete(folderId);
		} else {
			this.expanded.add(folderId);
		}
		this.persist();
	}

	/**
	 * Check if a folder is currently expanded.
	 */
	isExpanded(folderId: number): boolean {
		return this.expanded.has(folderId);
	}

	/**
	 * Persist current expansion state to localStorage.
	 */
	private persist() {
		if (typeof window !== 'undefined') {
			try {
				const ids = Array.from(this.expanded);
				localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
			} catch (error) {
				console.error('Failed to persist folder expansion state:', error);
			}
		}
	}
}

export const folderExpansion = new FolderExpansionState();
