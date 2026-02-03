import type { APIClient } from './client';
import type { FolderOut, FolderCreate, FolderUpdate } from '$lib/types/api';

/**
 * Folders API - handles all folder-related operations
 */
export class FoldersAPI {
	constructor(private client: APIClient) {}

	/**
	 * Get the complete folder tree with nested children
	 */
	async getTree(): Promise<FolderOut[]> {
		return this.client.get<FolderOut[]>('/folders/tree');
	}

	/**
	 * Get a single folder by ID
	 */
	async get(id: string): Promise<FolderOut> {
		return this.client.get<FolderOut>(`/folders/${id}`);
	}

	/**
	 * Create a new folder
	 */
	async create(data: FolderCreate): Promise<FolderOut> {
		const folder = await this.client.post<FolderOut>('/folders/', data);

		// Invalidate folder tree cache
		this.client.invalidateCache('folders/tree');

		return folder;
	}

	/**
	 * Update a folder (rename or move to different parent)
	 */
	async update(id: string, data: FolderUpdate): Promise<FolderOut> {
		const folder = await this.client.patch<FolderOut>(`/folders/${id}`, data);

		// Invalidate folder tree cache
		this.client.invalidateCache('folders/tree');

		return folder;
	}

	/**
	 * Delete a folder by ID
	 * Channels in this folder will be moved to root
	 * Child folders will be moved up one level
	 */
	async delete(id: string): Promise<void> {
		await this.client.delete(`/folders/${id}`);

		// Invalidate caches
		this.client.invalidateCache('folders/tree');
		this.client.invalidateCache('channels/');
	}
}
