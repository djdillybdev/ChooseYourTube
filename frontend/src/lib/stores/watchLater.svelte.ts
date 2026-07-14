import { getContext, setContext } from 'svelte';
import { api } from '$lib/api';
import type { PlaylistDetailOut } from '$lib/types/api';

const WATCH_LATER_CONTEXT = Symbol('watch-later');

export class WatchLaterState {
	playlist = $state<PlaylistDetailOut | null>(null);
	pendingIds = $state<string[]>([]);

	sync(playlist: PlaylistDetailOut | null) {
		this.playlist = playlist;
	}

	isSaved(videoId: string): boolean {
		return this.playlist?.video_ids.includes(videoId) ?? false;
	}

	isPending(videoId: string): boolean {
		return this.pendingIds.includes(videoId);
	}

	async setSaved(videoId: string, saved: boolean): Promise<void> {
		if (!this.playlist || this.isPending(videoId) || this.isSaved(videoId) === saved) return;

		const previousIds = [...this.playlist.video_ids];
		this.pendingIds = [...this.pendingIds, videoId];
		this.playlist = {
			...this.playlist,
			video_ids: saved
				? [...this.playlist.video_ids, videoId]
				: this.playlist.video_ids.filter((id) => id !== videoId),
			total_videos: this.playlist.total_videos + (saved ? 1 : -1)
		};

		try {
			if (saved) {
				this.playlist = await api.playlists.addWatchLater(videoId);
			} else {
				await api.playlists.removeWatchLater(videoId);
			}
		} catch (error) {
			if (this.playlist) {
				this.playlist = {
					...this.playlist,
					video_ids: previousIds,
					total_videos: previousIds.length
				};
			}
			throw error;
		} finally {
			this.pendingIds = this.pendingIds.filter((id) => id !== videoId);
		}
	}

	async toggle(videoId: string): Promise<void> {
		await this.setSaved(videoId, !this.isSaved(videoId));
	}
}

export function provideWatchLater(initial: PlaylistDetailOut | null): WatchLaterState {
	const state = new WatchLaterState();
	state.sync(initial);
	setContext(WATCH_LATER_CONTEXT, state);
	return state;
}

export function useWatchLater(): WatchLaterState {
	const state = getContext<WatchLaterState>(WATCH_LATER_CONTEXT);
	return state ?? new WatchLaterState();
}
