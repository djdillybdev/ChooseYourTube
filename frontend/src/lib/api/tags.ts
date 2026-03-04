import type { APIClient } from './client';
import type {
	TagOut,
	TagCreate,
	TagUpdate,
	TagFilters,
	PaginatedResponse,
	VideoOut,
	ChannelOut
} from '$lib/types/api';

/**
 * Tags API - handles all tag-related operations
 */
export class TagsAPI {
	constructor(private client: APIClient) {}

	/**
	 * List all tags with pagination
	 */
	async list(filters?: TagFilters): Promise<PaginatedResponse<TagOut>> {
		return this.client.get<PaginatedResponse<TagOut>>('/tags/', filters);
	}

	/**
	 * Get a single tag by ID
	 */
	async get(id: string): Promise<TagOut> {
		return this.client.get<TagOut>(`/tags/${id}`);
	}

	/**
	 * Create a new tag
	 */
	async create(data: TagCreate): Promise<TagOut> {
		const tag = await this.client.post<TagOut>('/tags/', data);

		// Invalidate tags list cache
		this.client.invalidateCache('tags/');

		return tag;
	}

	/**
	 * Update a tag's name
	 */
	async update(id: string, data: TagUpdate): Promise<TagOut> {
		const tag = await this.client.patch<TagOut>(`/tags/${id}`, data);

		// Invalidate caches
		this.client.invalidateCache('tags/');
		this.client.invalidateCache(`/tags/${id}`);

		return tag;
	}

	/**
	 * Delete a tag by ID
	 * This will also remove the tag from all associated channels and videos
	 */
	async delete(id: string): Promise<void> {
		await this.client.delete(`/tags/${id}`);

		// Invalidate caches (affects channels and videos too)
		this.client.invalidateCache('tags/');
		this.client.invalidateCache('channels/');
		this.client.invalidateCache('videos/');
	}

	/**
	 * Get all videos associated with a tag
	 */
	async getVideos(id: string, params?: { limit?: number; offset?: number }): Promise<VideoOut[]> {
		return this.client.get<VideoOut[]>(`/tags/${id}/videos`, params);
	}

	/**
	 * Get all channels associated with a tag
	 */
	async getChannels(
		id: string,
		params?: { limit?: number; offset?: number }
	): Promise<ChannelOut[]> {
		return this.client.get<ChannelOut[]>(`/tags/${id}/channels`, params);
	}
}
