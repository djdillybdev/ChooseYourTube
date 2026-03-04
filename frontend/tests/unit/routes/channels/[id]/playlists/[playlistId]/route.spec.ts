import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
	channelGetMock,
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

import { load } from '../../../../../../../src/routes/channels/[id]/playlists/[playlistId]/+page';

describe('channels/[id]/playlists/[playlistId] load', () => {
	beforeEach(() => {
		channelGetMock.mockReset();
		playlistGetMock.mockReset();
		videoGetMock.mockReset();
		createScopedAPIMock.mockReset();
		redirectMock.mockClear();
		errorMock.mockClear();

		createScopedAPIMock.mockReturnValue({
			channels: { get: channelGetMock },
			playlists: { get: playlistGetMock },
			videos: { get: videoGetMock }
		});
	});

	it('loads playlist videos in order and skips missing videos', async () => {
		channelGetMock.mockResolvedValue({ id: 'ch-1', title: 'Channel 1' });
		playlistGetMock.mockResolvedValue({
			id: 'pl-1',
			name: 'Uploads',
			source_channel_id: 'ch-1',
			video_ids: ['v1', 'v2', 'v3'],
			total_videos: 3
		});
		videoGetMock.mockImplementation((id: string) => {
			if (id === 'v2') {
				return Promise.reject(new Error('missing'));
			}
			return Promise.resolve({ id, title: `Video ${id}` });
		});

		const url = new URL('http://localhost/channels/ch-1/playlists/pl-1?page=1&pageSize=3');
		const result = (await load({
			params: { id: 'ch-1', playlistId: 'pl-1' },
			url,
			fetch: vi.fn()
		} as any)) as any;

		expect(result.videos).toEqual([
			{ id: 'v1', title: 'Video v1' },
			{ id: 'v3', title: 'Video v3' }
		]);
		expect(videoGetMock).toHaveBeenCalledTimes(3);
	});

	it('logs out and redirects on API 401', async () => {
		channelGetMock.mockRejectedValue(new APIErrorMock(401, { detail: 'unauthorized' }));
		playlistGetMock.mockResolvedValue({
			id: 'pl-1',
			source_channel_id: 'ch-1',
			video_ids: [],
			total_videos: 0
		});
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
		const url = new URL('http://localhost/channels/ch-1/playlists/pl-1');

		await expect(
			load({
				params: { id: 'ch-1', playlistId: 'pl-1' },
				url,
				fetch: fetchMock
			} as any)
		).rejects.toMatchObject({
			status: 307,
			location: '/login?next=%2Fchannels%2Fch-1%2Fplaylists%2Fpl-1'
		});
		expect(fetchMock).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' });
	});
});
