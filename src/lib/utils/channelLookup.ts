import type { ChannelOut } from '$lib/types/api';

/**
 * Creates a Map for O(1) channel lookups by ID
 */
export function createChannelMap(channels: ChannelOut[]): Map<string, ChannelOut> {
	return new Map(channels.map((ch) => [ch.id, ch]));
}

/**
 * Get channel title by ID with graceful fallback
 */
export function getChannelTitle(
	channelId: string,
	channelMap: Map<string, ChannelOut>
): string {
	return channelMap.get(channelId)?.title ?? `Channel ${channelId.slice(0, 8)}...`;
}
