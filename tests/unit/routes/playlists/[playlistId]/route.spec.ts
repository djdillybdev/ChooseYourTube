import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
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

import { load } from '../../../../../src/routes/playlists/[playlistId]/+page';

describe('/playlists/[playlistId] load', () => {
	beforeEach(() => {
		playlistGetMock.mockReset();
		videoGetMock.mockReset();
		createScopedAPIMock.mockReset();
		redirectMock.mockClear();
		errorMock.mockClear();

		createScopedAPIMock.mockReturnValue({
			playlists: { get: playlistGetMock },
			videos: { get: videoGetMock }
		});
	});

	it('hydrates videos in playlist order and skips missing', async () => {
		playlistGetMock.mockResolvedValue({
			id: 'pl-1',
			name: 'Manual',
			description: null,
			is_system: false,
			source_type: 'manual',
			source_channel_id: null,
			source_is_active: true,
			current_position: null,
			total_videos: 3,
			created_at: '2026-01-01T00:00:00Z',
			video_ids: ['v1', 'v2', 'v3']
		});
		videoGetMock.mockImplementation((id: string) => {
			if (id === 'v2') return Promise.reject(new Error('missing'));
			return Promise.resolve({ id, title: `Video ${id}` });
		});

		const result = (await load({
			params: { playlistId: 'pl-1' },
			url: new URL('http://localhost/playlists/pl-1'),
			fetch: vi.fn()
		} as any)) as any;

		expect(result.videos).toEqual([
			{ id: 'v1', title: 'Video v1' },
			{ id: 'v3', title: 'Video v3' }
		]);
	});

	it('rejects non-manual playlists with 404', async () => {
		playlistGetMock.mockResolvedValue({
			id: 'pl-1',
			name: 'Synced',
			description: null,
			is_system: false,
			source_type: 'channel',
			source_channel_id: 'ch-1',
			source_is_active: true,
			current_position: null,
			total_videos: 0,
			created_at: '2026-01-01T00:00:00Z',
			video_ids: []
		});

		await expect(
			load({
				params: { playlistId: 'pl-1' },
				url: new URL('http://localhost/playlists/pl-1'),
				fetch: vi.fn()
			} as any)
		).rejects.toMatchObject({ status: 404 });
	});

	it('logs out and redirects on API 401', async () => {
		playlistGetMock.mockRejectedValue(new APIErrorMock(401, { detail: 'unauthorized' }));
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));

		await expect(
			load({
				params: { playlistId: 'pl-1' },
				url: new URL('http://localhost/playlists/pl-1'),
				fetch: fetchMock
			} as any)
		).rejects.toMatchObject({
			status: 307,
			location: '/login?next=%2Fplaylists%2Fpl-1'
		});
		expect(fetchMock).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' });
	});
});
