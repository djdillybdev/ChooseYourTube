import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
	channelGetMock,
	channelListPlaylistsMock,
	playlistGetMock,
	videoGetMock,
	createScopedAPIMock,
	redirectMock,
	errorMock,
	APIErrorMock
} = vi.hoisted(() => {
	class APIErrorMock extends Error {
		status: number;
		detail: unknown;
		constructor(status: number, detail: unknown) {
			super(`API Error ${status}`);
			this.status = status;
			this.detail = detail;
		}
	}

	return {
		channelGetMock: vi.fn(),
		channelListPlaylistsMock: vi.fn(),
		playlistGetMock: vi.fn(),
		videoGetMock: vi.fn(),
		createScopedAPIMock: vi.fn(),
		redirectMock: vi.fn((status: number, location: string) => {
			const err = new Error('redirect') as Error & { status: number; location: string };
			err.status = status;
			err.location = location;
			throw err;
		}),
		errorMock: vi.fn((status: number, message: string) => {
			const err = new Error(message) as Error & { status: number };
			err.status = status;
			throw err;
		}),
		APIErrorMock
	};
});

vi.mock('$lib/api', () => ({
	APIError: APIErrorMock,
	createScopedAPI: createScopedAPIMock
}));

vi.mock('@sveltejs/kit', () => ({
	redirect: redirectMock,
	error: errorMock
}));

import { load } from '../../../../../../src/routes/channels/[id]/playlists/+page';

describe('channels/[id]/playlists load', () => {
	beforeEach(() => {
		channelGetMock.mockReset();
		channelListPlaylistsMock.mockReset();
		playlistGetMock.mockReset();
		videoGetMock.mockReset();
		createScopedAPIMock.mockReset();
		redirectMock.mockClear();
		errorMock.mockClear();

		createScopedAPIMock.mockReturnValue({
			channels: {
				get: channelGetMock,
				listPlaylists: channelListPlaylistsMock
			},
			playlists: {
				get: playlistGetMock
			},
			videos: {
				get: videoGetMock
			}
		});
	});

	it('loads channel and playlists with direct thumbnails', async () => {
		channelGetMock.mockResolvedValue({ id: 'ch-1', title: 'Channel 1' });
		channelListPlaylistsMock.mockResolvedValue({
			items: [
				{
					id: 'pl-1',
					name: 'Uploads',
					description: null,
					thumbnail_url: 'https://img.example/direct.jpg',
					is_system: false,
					source_type: 'channel',
					source_channel_id: 'ch-1',
					source_youtube_playlist_id: 'yt-1',
					source_is_active: true,
					source_last_synced_at: null,
					total_videos: 10,
					created_at: '2026-02-01T00:00:00Z'
				}
			],
			total: 1
		});
		const url = new URL('http://localhost/channels/ch-1/playlists?page=2&pageSize=12');
		const fetchMock = vi.fn();

		const result = (await load({ params: { id: 'ch-1' }, url, fetch: fetchMock } as any)) as any;

		expect(channelGetMock).toHaveBeenCalledWith('ch-1');
		expect(channelListPlaylistsMock).toHaveBeenCalledWith('ch-1', {
			include_inactive: false,
			limit: 12,
			offset: 12
		});
		expect(playlistGetMock).not.toHaveBeenCalled();
		expect(videoGetMock).not.toHaveBeenCalled();
		expect(result).toEqual({
			channel: { id: 'ch-1', title: 'Channel 1' },
			playlists: [
				{
					id: 'pl-1',
					name: 'Uploads',
					description: null,
					thumbnail_url: 'https://img.example/direct.jpg',
					display_thumbnail_url: 'https://img.example/direct.jpg',
					is_system: false,
					source_type: 'channel',
					source_channel_id: 'ch-1',
					source_youtube_playlist_id: 'yt-1',
					source_is_active: true,
					source_last_synced_at: null,
					total_videos: 10,
					created_at: '2026-02-01T00:00:00Z'
				}
			],
			total: 1,
			page: 2,
			pageSize: 12
		});
	});

	it('falls back to first video thumbnail when playlist thumbnail is missing', async () => {
		channelGetMock.mockResolvedValue({ id: 'ch-1', title: 'Channel 1' });
		channelListPlaylistsMock.mockResolvedValue({
			items: [
				{
					id: 'pl-1',
					name: 'Uploads',
					description: null,
					thumbnail_url: null,
					is_system: false,
					source_type: 'channel',
					source_channel_id: 'ch-1',
					source_youtube_playlist_id: 'yt-1',
					source_is_active: true,
					source_last_synced_at: null,
					total_videos: 3,
					created_at: '2026-02-01T00:00:00Z'
				}
			],
			total: 1
		});
		playlistGetMock.mockResolvedValue({ video_ids: ['v-1'] });
		videoGetMock.mockResolvedValue({ id: 'v-1', thumbnail_url: 'https://img.example/video.jpg' });
		const url = new URL('http://localhost/channels/ch-1/playlists?page=1&pageSize=24');
		const fetchMock = vi.fn();

		const result = (await load({ params: { id: 'ch-1' }, url, fetch: fetchMock } as any)) as any;

		expect(playlistGetMock).toHaveBeenCalledWith('pl-1');
		expect(videoGetMock).toHaveBeenCalledWith('v-1');
		expect(result.playlists[0]?.display_thumbnail_url).toBe('https://img.example/video.jpg');
	});

	it('keeps loading when thumbnail fallback lookup fails', async () => {
		channelGetMock.mockResolvedValue({ id: 'ch-1', title: 'Channel 1' });
		channelListPlaylistsMock.mockResolvedValue({
			items: [
				{
					id: 'pl-1',
					name: 'Uploads',
					description: null,
					thumbnail_url: null,
					is_system: false,
					source_type: 'channel',
					source_channel_id: 'ch-1',
					source_youtube_playlist_id: 'yt-1',
					source_is_active: true,
					source_last_synced_at: null,
					total_videos: 3,
					created_at: '2026-02-01T00:00:00Z'
				}
			],
			total: 1
		});
		playlistGetMock.mockRejectedValue(new Error('playlist lookup failed'));
		const url = new URL('http://localhost/channels/ch-1/playlists?page=1');
		const fetchMock = vi.fn();

		const result = (await load({ params: { id: 'ch-1' }, url, fetch: fetchMock } as any)) as any;

		expect(result.playlists[0]?.display_thumbnail_url).toBeNull();
	});

	it('logs out and redirects on API 401', async () => {
		channelGetMock.mockRejectedValue(new APIErrorMock(401, { detail: 'unauthorized' }));
		channelListPlaylistsMock.mockResolvedValue({ items: [], total: 0 });
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
		const url = new URL('http://localhost/channels/ch-1/playlists?page=1');

		await expect(load({ params: { id: 'ch-1' }, url, fetch: fetchMock } as any)).rejects.toMatchObject({
			status: 307,
			location: '/login?next=%2Fchannels%2Fch-1%2Fplaylists%3Fpage%3D1'
		});
		expect(fetchMock).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' });
	});
});
