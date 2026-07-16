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

	async listByIds(ids: string[]): Promise<VideoOut[]> {
		const uniqueIds = [...new Set(ids)];
		const chunks: string[][] = [];
		for (let index = 0; index < uniqueIds.length; index += 200) {
			chunks.push(uniqueIds.slice(index, index + 200));
		}
		const responses = await Promise.all(
			chunks.map((chunk) => this.list({ video_ids: chunk.join(','), limit: chunk.length }))
		);
		return responses.flatMap((response) => response.items);
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
