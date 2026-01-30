import { api } from '$lib/api';
import type { FolderOut } from '$lib/types/api';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ depends }) => {
	depends('app:folders');
	depends('app:channels');

	try {
		const folders = await api.folders.getTree();
		return {
			folders
		};
	} catch (error) {
		console.error('Failed to load folders:', error);
		// Return empty array on error to prevent layout from breaking
		return {
			folders: [] as FolderOut[]
		};
	}
};
