import { api } from '$lib/api';
import type { PlaylistDetailOut, PlaylistOut, VideoOut } from '$lib/types/api';

const QUEUE_NAME = 'Queue';

function findQueuePlaylist(playlists: PlaylistOut[]): PlaylistOut | undefined {
	return playlists.find((playlist) => playlist.is_system && playlist.name === QUEUE_NAME);
}

export async function ensureQueuePlaylist(): Promise<PlaylistOut> {
	const response = await api.playlists.list({ is_system: true, limit: 200, offset: 0 });
	const existing = findQueuePlaylist(response.items);
	if (existing) {
		return existing;
	}

	return api.playlists.create({
		name: QUEUE_NAME,
		description: 'System queue playlist for playback',
		is_system: true
	});
}

export async function loadQueueDetail(playlistId: string): Promise<PlaylistDetailOut> {
	return api.playlists.get(playlistId);
}

export async function hydrateQueueVideos(videoIds: string[]): Promise<VideoOut[]> {
	if (!videoIds.length) return [];

	const byId = new Map<string, VideoOut>();
	const results = await Promise.allSettled(videoIds.map((id) => api.videos.get(id)));

	for (const result of results) {
		if (result.status === 'fulfilled') {
			byId.set(result.value.id, result.value);
		}
	}

	return videoIds.map((id) => byId.get(id)).filter((video): video is VideoOut => Boolean(video));
}

export async function addVideoToQueue(
	playlistId: string,
	videoId: string,
	position?: number
): Promise<PlaylistDetailOut> {
	return api.playlists.addVideo(playlistId, {
		video_id: videoId,
		position
	});
}

export async function setQueuePosition(
	playlistId: string,
	position: number | null
): Promise<PlaylistDetailOut> {
	return api.playlists.setPosition(playlistId, {
		current_position: position
	});
}

export async function removeVideoFromQueue(
	playlistId: string,
	videoId: string
): Promise<PlaylistDetailOut> {
	await api.playlists.removeVideo(playlistId, videoId);
	return api.playlists.get(playlistId);
}

export async function moveQueueVideo(
	playlistId: string,
	videoId: string,
	newPosition: number
): Promise<PlaylistDetailOut> {
	return api.playlists.moveVideo(playlistId, {
		video_id: videoId,
		new_position: newPosition
	});
}

export async function clearQueueVideos(playlistId: string): Promise<PlaylistDetailOut> {
	return api.playlists.clearVideos(playlistId);
}

export async function replaceQueueVideos(
	playlistId: string,
	videoIds: string[]
): Promise<PlaylistDetailOut> {
	return api.playlists.setVideos(playlistId, { video_ids: videoIds });
}
