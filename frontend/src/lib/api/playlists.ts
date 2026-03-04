import type { APIClient } from './client';
import type {
	PaginatedResponse,
	PlaylistAddVideo,
	PlaylistAddVideos,
	PlaylistCreate,
	PlaylistDetailOut,
	PlaylistFilters,
	PlaylistMoveVideo,
	PlaylistOut,
	PlaylistSetPosition,
	PlaylistSetVideos,
	PlaylistUpdate
} from '$lib/types/api';

/**
 * Playlists API - handles playlist operations used for queue management.
 */
export class PlaylistsAPI {
	constructor(private client: APIClient) {}

	async list(filters?: PlaylistFilters): Promise<PaginatedResponse<PlaylistOut>> {
		return this.client.get<PaginatedResponse<PlaylistOut>>('/playlists/', filters);
	}

	async create(data: PlaylistCreate): Promise<PlaylistOut> {
		const playlist = await this.client.post<PlaylistOut>('/playlists/', data);
		this.client.invalidateCache('playlists/');
		return playlist;
	}

	async get(id: string): Promise<PlaylistDetailOut> {
		return this.client.get<PlaylistDetailOut>(`/playlists/${id}`);
	}

	async update(id: string, data: PlaylistUpdate): Promise<PlaylistOut> {
		const playlist = await this.client.patch<PlaylistOut>(`/playlists/${id}`, data);
		this.client.invalidateCache('playlists/');
		this.client.invalidateCache(`/playlists/${id}`);
		return playlist;
	}

	async delete(id: string): Promise<void> {
		await this.client.delete(`/playlists/${id}`);
		this.client.invalidateCache('playlists/');
		this.client.invalidateCache(`/playlists/${id}`);
	}

	async setVideos(id: string, data: PlaylistSetVideos): Promise<PlaylistDetailOut> {
		const playlist = await this.client.put<PlaylistDetailOut>(`/playlists/${id}/videos`, data);
		this.client.invalidateCache(`/playlists/${id}`);
		return playlist;
	}

	async addVideo(id: string, data: PlaylistAddVideo): Promise<PlaylistDetailOut> {
		const playlist = await this.client.post<PlaylistDetailOut>(`/playlists/${id}/videos`, data);
		this.client.invalidateCache(`/playlists/${id}`);
		return playlist;
	}

	async bulkAddVideos(id: string, data: PlaylistAddVideos): Promise<PlaylistDetailOut> {
		const playlist = await this.client.post<PlaylistDetailOut>(`/playlists/${id}/videos/bulk`, data);
		this.client.invalidateCache(`/playlists/${id}`);
		return playlist;
	}

	async clearVideos(id: string): Promise<PlaylistDetailOut> {
		const playlist = await this.client.fetch<PlaylistDetailOut>(`/playlists/${id}/videos`, {
			method: 'DELETE',
			cacheTTL: 0
		});
		this.client.invalidateCache(`/playlists/${id}`);
		return playlist;
	}

	async moveVideo(id: string, data: PlaylistMoveVideo): Promise<PlaylistDetailOut> {
		const playlist = await this.client.patch<PlaylistDetailOut>(`/playlists/${id}/videos/move`, data);
		this.client.invalidateCache(`/playlists/${id}`);
		return playlist;
	}

	async setPosition(id: string, data: PlaylistSetPosition): Promise<PlaylistDetailOut> {
		const playlist = await this.client.patch<PlaylistDetailOut>(`/playlists/${id}/position`, data);
		this.client.invalidateCache(`/playlists/${id}`);
		return playlist;
	}

	async shuffle(id: string): Promise<PlaylistDetailOut> {
		const playlist = await this.client.post<PlaylistDetailOut>(`/playlists/${id}/shuffle`);
		this.client.invalidateCache(`/playlists/${id}`);
		return playlist;
	}

	async removeVideo(id: string, videoId: string): Promise<void> {
		await this.client.delete(`/playlists/${id}/videos/${videoId}`);
		this.client.invalidateCache(`/playlists/${id}`);
	}
}
