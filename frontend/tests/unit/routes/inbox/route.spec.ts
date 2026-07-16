import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
	invalidateMock,
	listMock,
	createScopedAPIMock,
	parseVideoFilterQueryMock,
	redirectMock,
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
		invalidateMock: vi.fn(),
		listMock: vi.fn(),
		createScopedAPIMock: vi.fn(),
		parseVideoFilterQueryMock: vi.fn(),
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
	api: { invalidate: invalidateMock },
	APIError: APIErrorMock,
	createScopedAPI: createScopedAPIMock
}));

vi.mock('$lib/utils/videoFilterQuery', () => ({
	parseVideoFilterQuery: parseVideoFilterQueryMock
}));

vi.mock('@sveltejs/kit', () => ({
	redirect: redirectMock
}));

import { load } from '../../../../src/routes/inbox/+page';

describe('inbox load', () => {
	beforeEach(() => {
		invalidateMock.mockReset();
		listMock.mockReset();
		createScopedAPIMock.mockReset();
		parseVideoFilterQueryMock.mockReset();
		redirectMock.mockClear();

		createScopedAPIMock.mockReturnValue({ videos: { list: listMock } });
		parseVideoFilterQueryMock.mockReturnValue({ apiFilters: { is_watched: false }, uiFilters: {} });
	});

	it('loads paginated videos with parsed filters', async () => {
		listMock.mockResolvedValue({ items: [{ id: 'v1' }], total: 1 });
		const fetchMock = vi.fn();
		const url = new URL('http://localhost/inbox?page=2&pageSize=12&q=test');

		const result = await load({ url, fetch: fetchMock, parent: vi.fn() } as any);

		expect(invalidateMock).toHaveBeenCalledWith('videos/');
		expect(parseVideoFilterQueryMock).toHaveBeenCalledWith(url, { defaultWatched: false });
		expect(listMock).toHaveBeenCalledWith({
			is_watched: false,
			q: 'test',
			limit: 12,
			offset: 12
		});
		expect(result).toEqual({
			videos: [{ id: 'v1' }],
			total: 1,
			page: 2,
			pageSize: 12,
			q: 'test'
		});
	});

	it('logs out and redirects on API 401', async () => {
		listMock.mockRejectedValue(new APIErrorMock(401, { detail: 'nope' }));
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
		const url = new URL('http://localhost/inbox?page=3');

		await expect(load({ url, fetch: fetchMock, parent: vi.fn() } as any)).rejects.toMatchObject({
			status: 307,
			location: '/login?next=%2Finbox%3Fpage%3D3'
		});
		expect(fetchMock).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' });
	});

	it('returns fallback payload on non-auth errors', async () => {
		listMock.mockRejectedValue(new Error('boom'));
		const fetchMock = vi.fn();
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
		const url = new URL('http://localhost/inbox?page=-1&pageSize=48');

		const result = await load({ url, fetch: fetchMock, parent: vi.fn() } as any);

		expect(result).toEqual({
			videos: [],
			total: 0,
			page: 1,
			pageSize: 48,
			q: undefined,
			error: 'boom'
		});
		consoleErrorSpy.mockRestore();
	});
});
