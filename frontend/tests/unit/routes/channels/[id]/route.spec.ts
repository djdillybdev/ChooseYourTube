import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
	channelGetMock,
	videosListMock,
	createScopedAPIMock,
	parseVideoFilterQueryMock,
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
		videosListMock: vi.fn(),
		createScopedAPIMock: vi.fn(),
		parseVideoFilterQueryMock: vi.fn(),
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

vi.mock('$lib/utils/videoFilterQuery', () => ({
	parseVideoFilterQuery: parseVideoFilterQueryMock
}));

vi.mock('@sveltejs/kit', () => ({
	redirect: redirectMock,
	error: errorMock
}));

import { load } from '../../../../../src/routes/channels/[id]/+page';

describe('channels/[id] load', () => {
	beforeEach(() => {
		channelGetMock.mockReset();
		videosListMock.mockReset();
		createScopedAPIMock.mockReset();
		parseVideoFilterQueryMock.mockReset();
		redirectMock.mockClear();
		errorMock.mockClear();

		createScopedAPIMock.mockReturnValue({
			channels: { get: channelGetMock },
			videos: { list: videosListMock }
		});
		parseVideoFilterQueryMock.mockReturnValue({
			apiFilters: { channel_id: 'ch-1' },
			uiFilters: {}
		});
	});

	it('loads channel and videos with forced channel filters', async () => {
		channelGetMock.mockResolvedValue({ id: 'ch-1', title: 'Channel 1' });
		videosListMock.mockResolvedValue({ items: [{ id: 'v1' }], total: 1 });
		const fetchMock = vi.fn();
		const url = new URL('http://localhost/channels/ch-1?page=2&pageSize=12&q=svelte');

		const result = await load({
			params: { id: 'ch-1' },
			url,
			fetch: fetchMock,
			parent: vi.fn()
		} as any);

		expect(parseVideoFilterQueryMock).toHaveBeenCalledWith(url, { forcedChannelId: 'ch-1' });
		expect(channelGetMock).toHaveBeenCalledWith('ch-1');
		expect(videosListMock).toHaveBeenCalledWith({
			channel_id: 'ch-1',
			q: 'svelte',
			limit: 12,
			offset: 12
		});
		expect(result).toEqual({
			channel: { id: 'ch-1', title: 'Channel 1' },
			videos: [{ id: 'v1' }],
			total: 1,
			page: 2,
			pageSize: 12,
			q: 'svelte'
		});
	});

	it('logs out and redirects on API 401', async () => {
		channelGetMock.mockRejectedValue(new APIErrorMock(401, { detail: 'unauthorized' }));
		videosListMock.mockResolvedValue({ items: [], total: 0 });
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
		const url = new URL('http://localhost/channels/ch-1?q=x');

		await expect(
			load({ params: { id: 'ch-1' }, url, fetch: fetchMock, parent: vi.fn() } as any)
		).rejects.toMatchObject({
			status: 307,
			location: '/login?next=%2Fchannels%2Fch-1%3Fq%3Dx'
		});
		expect(fetchMock).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' });
	});

	it('throws 404 only when the backend reports that the channel is missing', async () => {
		channelGetMock.mockRejectedValue(new APIErrorMock(404, { detail: 'missing' }));
		videosListMock.mockResolvedValue({ items: [], total: 0 });
		const fetchMock = vi.fn();
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
		const url = new URL('http://localhost/channels/ch-missing');

		await expect(
			load({ params: { id: 'ch-missing' }, url, fetch: fetchMock, parent: vi.fn() } as any)
		).rejects.toMatchObject({
			status: 404,
			message: 'Channel not found'
		});

		expect(errorMock).toHaveBeenCalledWith(404, 'Channel not found');
		consoleErrorSpy.mockRestore();
	});

	it('reports transport failures as a bad gateway instead of a false 404', async () => {
		channelGetMock.mockResolvedValue({ id: 'ch-1', title: 'Channel 1' });
		videosListMock.mockRejectedValue(new TypeError('Decoding failed'));
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);

		await expect(
			load({
				params: { id: 'ch-1' },
				url: new URL('http://localhost/channels/ch-1'),
				fetch: vi.fn(),
				parent: vi.fn()
			} as any)
		).rejects.toMatchObject({
			status: 502,
			message: 'Channel videos could not be loaded. Please retry.'
		});

		expect(errorMock).toHaveBeenCalledWith(
			502,
			'Channel videos could not be loaded. Please retry.'
		);
		consoleErrorSpy.mockRestore();
	});
});
