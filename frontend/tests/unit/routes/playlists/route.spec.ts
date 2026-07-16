import { beforeEach, describe, expect, it, vi } from 'vitest';

const { playlistListMock, createScopedAPIMock, redirectMock, APIErrorMock } = vi.hoisted(() => {
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
		playlistListMock: vi.fn(),
		createScopedAPIMock: vi.fn(),
		redirectMock: vi.fn((status: number, location: string) => {
			const err = new Error('redirect') as Error & { status: number; location: string };
			err.status = status;
			err.location = location;
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
	redirect: redirectMock
}));

import { load } from '../../../../src/routes/playlists/+page';

describe('/playlists load', () => {
	beforeEach(() => {
		playlistListMock.mockReset();
		createScopedAPIMock.mockReset();
		redirectMock.mockClear();

		createScopedAPIMock.mockReturnValue({
			playlists: {
				list: playlistListMock
			}
		});
	});

	it('loads manual playlists from enriched list metadata without per-card requests', async () => {
		playlistListMock.mockResolvedValue({
			items: [
				{
					id: 'pl-manual',
					name: 'Manual',
					description: 'mine',
					thumbnail_url: null,
					is_system: false,
					source_type: 'manual',
					source_channel_id: null,
					source_youtube_playlist_id: null,
					source_is_active: true,
					source_last_synced_at: null,
					total_videos: 1,
					preview_thumbnail_url: 'https://img.example/v1.jpg',
					created_at: '2026-01-01T00:00:00Z'
				},
				{
					id: 'pl-channel',
					name: 'Synced',
					description: null,
					thumbnail_url: null,
					is_system: false,
					source_type: 'channel',
					source_channel_id: 'ch-1',
					source_youtube_playlist_id: 'yt-1',
					source_is_active: true,
					source_last_synced_at: null,
					total_videos: 2,
					preview_thumbnail_url: null,
					created_at: '2026-01-01T00:00:00Z'
				}
			],
			total: 2,
			limit: 200,
			offset: 0,
			has_more: false
		});
		const url = new URL('http://localhost/playlists?page=1&pageSize=24');
		const result = (await load({ url, fetch: vi.fn(), parent: vi.fn() } as any)) as any;

		expect(result.total).toBe(1);
		expect(result.playlists).toHaveLength(1);
		expect(result.playlists[0].id).toBe('pl-manual');
		expect(result.playlists[0].display_thumbnail_url).toBe('https://img.example/v1.jpg');
	});

	it('logs out and redirects on API 401', async () => {
		playlistListMock.mockRejectedValue(new APIErrorMock(401, { detail: 'unauthorized' }));
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
		const url = new URL('http://localhost/playlists?page=2');

		await expect(load({ url, fetch: fetchMock, parent: vi.fn() } as any)).rejects.toMatchObject({
			status: 307,
			location: '/login?next=%2Fplaylists%3Fpage%3D2'
		});
		expect(fetchMock).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' });
	});
});
