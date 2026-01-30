import { apiClient, APIClient } from './client';
import { VideosAPI } from './videos';
import { ChannelsAPI } from './channels';
import { FoldersAPI } from './folders';
import { TagsAPI } from './tags';

/**
 * Unified API interface providing access to all backend resources
 */
interface API {
	videos: VideosAPI;
	channels: ChannelsAPI;
	folders: FoldersAPI;
	tags: TagsAPI;
	invalidateAll: () => void;
	invalidate: (pattern: string) => void;
}

/**
 * Create a new API instance with a custom base client
 */
function createAPI(client: APIClient): API {
	return {
		videos: new VideosAPI(client),
		channels: new ChannelsAPI(client),
		folders: new FoldersAPI(client),
		tags: new TagsAPI(client),
		invalidateAll: () => client.invalidateCache(),
		invalidate: (pattern: string) => client.invalidateCache(pattern)
	};
}

/**
 * Default API instance using the singleton client
 * This is what you'll import in your components
 */
export const api = createAPI(apiClient);

/**
 * Export the factory function for testing or custom instances
 */
export { createAPI };

/**
 * Re-export types for convenience
 */
export type { API };
export * from '$lib/types/api';
