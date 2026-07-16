import { beforeEach, describe, expect, it, vi } from 'vitest';

const { videosListMock, errorMock, redirectMock } = vi.hoisted(() => ({
	videosListMock: vi.fn(),
	errorMock: vi.fn((status: number, message: string) => {
		const failure = new Error(message) as Error & { status: number };
		failure.status = status;
		throw failure;
	}),
	redirectMock: vi.fn()
}));

vi.mock('$lib/api', () => ({
	APIError: class APIError extends Error {},
	createScopedAPI: () => ({ videos: { list: videosListMock } })
}));

vi.mock('$lib/utils/videoFilterQuery', () => ({
	parseVideoFilterQuery: () => ({ apiFilters: {}, uiFilters: {} })
}));

vi.mock('@sveltejs/kit', () => ({ error: errorMock, redirect: redirectMock }));

import { load } from '../../../../../src/routes/categories/[id]/+page';

describe('categories/[id] load', () => {
	beforeEach(() => {
		videosListMock.mockReset();
		errorMock.mockClear();
	});

	it('uses category membership to load the combined video feed', async () => {
		videosListMock.mockResolvedValue({ items: [{ id: 'video-1' }], total: 1 });
		const categories = [
			{ id: 'games', name: 'Games', channel_ids: ['channel-1'], created_at: '2026-01-01' }
		];
		const channels = [
			{ id: 'channel-1', title: 'One' },
			{ id: 'channel-2', title: 'Two' }
		];

		const result = await load({
			params: { id: 'games' },
			url: new URL('http://localhost/categories/games'),
			fetch: vi.fn(),
			parent: vi.fn().mockResolvedValue({ categories, channels })
		} as any);

		expect(result).toMatchObject({ channels: [channels[0]], total: 1 });
		expect(videosListMock).toHaveBeenCalledWith(
			expect.objectContaining({ channel_id: 'channel-1', limit: 24, offset: 0 })
		);
	});

	it('returns 404 when the category is absent from the loaded collection', async () => {
		await expect(
			load({
				params: { id: 'missing' },
				url: new URL('http://localhost/categories/missing'),
				fetch: vi.fn(),
				parent: vi.fn().mockResolvedValue({ categories: [], channels: [] })
			} as any)
		).rejects.toMatchObject({ status: 404, message: 'Category not found' });
	});
});
