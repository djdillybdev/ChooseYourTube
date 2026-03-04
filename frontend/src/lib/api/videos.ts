import type { APIClient } from './client';
import type { VideoOut, VideoUpdate, VideoFilters, PaginatedResponse } from '$lib/types/api';

/**
 * Videos API - handles all video-related operations
 */
export class VideosAPI {
	constructor(private client: APIClient) {}

	/**
	 * List videos with optional filtering and pagination
	 */
	async list(filters?: VideoFilters): Promise<PaginatedResponse<VideoOut>> {
		return this.client.get<PaginatedResponse<VideoOut>>('/videos/', filters);
	}

	/**
	 * Get a single video by ID
	 */
	async get(id: string): Promise<VideoOut> {
		return this.client.get<VideoOut>(`/videos/${id}`);
	}

	/**
	 * Update video metadata (favorited, watched, short status, tags)
	 */
	async update(id: string, data: VideoUpdate): Promise<VideoOut> {
		const video = await this.client.patch<VideoOut>(`/videos/${id}`, data);

		// Invalidate video list caches after update
		this.client.invalidateCache('videos/');
		this.client.invalidateCache(`/videos/${id}`);

		return video;
	}

	/**
	 * Delete a video by ID
	 */
	async delete(id: string): Promise<void> {
		await this.client.delete(`/videos/${id}`);

		// Invalidate caches
		this.client.invalidateCache('videos/');
	}

	/**
	 * List videos for a specific channel
	 */
	async listByChannel(
		channelId: string,
		params?: { limit?: number; offset?: number }
	): Promise<VideoOut[]> {
		return this.client.get<VideoOut[]>(`/videos/by-channel/${channelId}`, params);
	}
}
