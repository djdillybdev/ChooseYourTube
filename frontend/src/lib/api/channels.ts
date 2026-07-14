import type { APIClient } from './client';
import type {
	ChannelOut,
	SyncRunOut,
	ChannelPlaylistFilters,
	ChannelPlaylistOut,
	ChannelCreate,
	ChannelUpdate,
	ChannelFilters,
	PaginatedResponse
} from '$lib/types/api';

/**
 * Channels API - handles all channel-related operations
 */
export class ChannelsAPI {
	constructor(private client: APIClient) {}

	/**
	 * List channels with optional filtering and pagination
	 */
	async list(filters?: ChannelFilters): Promise<PaginatedResponse<ChannelOut>> {
		return this.client.get<PaginatedResponse<ChannelOut>>('/channels/', filters);
	}

	/**
	 * Get a single channel by ID
	 */
	async get(id: string): Promise<ChannelOut> {
		return this.client.get<ChannelOut>(`/channels/${id}`);
	}

	/**
	 * Create a new channel
	 */
	async create(data: ChannelCreate): Promise<ChannelOut> {
		const channel = await this.client.post<ChannelOut>('/channels/', data);

		// Invalidate channel list cache
		this.client.invalidateCache('channels/');

		return channel;
	}

	/**
	 * Update channel metadata (favorited, folder, tags)
	 */
	async update(id: string, data: ChannelUpdate): Promise<ChannelOut> {
		const channel = await this.client.patch<ChannelOut>(`/channels/${id}`, data);

		// Invalidate caches
		this.client.invalidateCache('channels/');
		this.client.invalidateCache(`/channels/${id}`);

		return channel;
	}

	/**
	 * Delete a channel by ID
	 */
	async delete(id: string): Promise<void> {
		await this.client.delete(`/channels/${id}`);

		// Invalidate caches (videos will also be deleted)
		this.client.invalidateCache('channels/');
		this.client.invalidateCache('videos/');
	}

	/**
	 * Refresh a channel to fetch latest videos from YouTube
	 */
	async refresh(id: string): Promise<SyncRunOut> {
		const channel = await this.client.post<SyncRunOut>(`/channels/${id}/refresh`);

		// Invalidate caches (new videos fetched)
		this.client.invalidateCache(`/channels/${id}`);
		this.client.invalidateCache('videos/');

		return channel;
	}

	/**
	 * List synced playlists for a channel.
	 */
	async listPlaylists(
		channelId: string,
		filters?: ChannelPlaylistFilters
	): Promise<PaginatedResponse<ChannelPlaylistOut>> {
		return this.client.get<PaginatedResponse<ChannelPlaylistOut>>(
			`/channels/${channelId}/playlists`,
			filters
		);
	}

	/**
	 * Refresh synced playlists for a channel.
	 */
	async refreshPlaylists(channelId: string): Promise<SyncRunOut> {
		const run = await this.client.post<SyncRunOut>(`/channels/${channelId}/playlists/refresh`);
		this.client.invalidateCache(`/channels/${channelId}/playlists`);
		return run;
	}

	/**
	 * Delete all channels (requires confirmation)
	 * WARNING: This is a destructive operation for testing
	 */
	async deleteAll(confirm: string): Promise<void> {
		if (confirm !== 'DELETE_ALL_CHANNELS') {
			throw new Error('Must confirm with exact string: DELETE_ALL_CHANNELS');
		}

		await this.client.delete(`/channels/?confirm=${confirm}`);

		// Clear all caches
		this.client.invalidateCache();
	}
}
