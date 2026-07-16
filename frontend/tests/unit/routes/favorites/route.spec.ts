import { beforeEach, describe, expect, it, vi } from 'vitest';

const { videosListMock, redirectMock } = vi.hoisted(() => ({
	videosListMock: vi.fn(),
	redirectMock: vi.fn()
}));

vi.mock('$lib/api', () => ({
	APIError: class APIError extends Error {},
	createScopedAPI: () => ({ videos: { list: videosListMock } })
}));

vi.mock('$lib/utils/videoFilterQuery', () => ({
	parseVideoFilterQuery: () => ({ apiFilters: {}, uiFilters: {} })
}));

vi.mock('@sveltejs/kit', () => ({ redirect: redirectMock }));

import { load } from '../../../../src/routes/favorites/+page';

describe('favorites load', () => {
	beforeEach(() => {
		videosListMock.mockReset();
	});

	it('loads the combined feed for favorited channels only', async () => {
		videosListMock.mockResolvedValue({ items: [{ id: 'video-1' }], total: 1 });
		const channels = [
			{ id: 'favorite-2', title: 'Zulu', is_favorited: true },
			{ id: 'regular', title: 'Middle', is_favorited: false },
			{ id: 'favorite-1', title: 'Alpha', is_favorited: true }
		];

		const result = await load({
			url: new URL('http://localhost/favorites?page=2&pageSize=10&q=recent'),
			fetch: vi.fn(),
			parent: vi.fn().mockResolvedValue({ channels })
		} as any);

		expect(result).toMatchObject({
			channels: [channels[2], channels[0]],
			total: 1,
			page: 2,
			pageSize: 10,
			q: 'recent'
		});
		expect(videosListMock).toHaveBeenCalledWith(
			expect.objectContaining({
				channel_id: 'favorite-1,favorite-2',
				q: 'recent',
				limit: 10,
				offset: 10
			})
		);
	});

	it('does not request videos when there are no favorites', async () => {
		const result = await load({
			url: new URL('http://localhost/favorites'),
			fetch: vi.fn(),
			parent: vi.fn().mockResolvedValue({
				channels: [{ id: 'regular', title: 'Regular', is_favorited: false }]
			})
		} as any);

		expect(result).toMatchObject({ channels: [], videos: [], total: 0 });
		expect(videosListMock).not.toHaveBeenCalled();
	});
});
