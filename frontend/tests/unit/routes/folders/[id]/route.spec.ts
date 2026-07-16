import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
	folderGetMock,
	channelsListMock,
	videosListMock,
	createScopedAPIMock,
	parseVideoFilterQueryMock,
	redirectMock,
	errorMock,
	APIErrorMock
} = vi.hoisted(() => {
	class APIErrorMock extends Error {
		status: number;
		constructor(status: number) {
			super(`API Error ${status}`);
			this.status = status;
		}
	}

	return {
		folderGetMock: vi.fn(),
		channelsListMock: vi.fn(),
		videosListMock: vi.fn(),
		createScopedAPIMock: vi.fn(),
		parseVideoFilterQueryMock: vi.fn(),
		redirectMock: vi.fn(),
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

import { load } from '../../../../../src/routes/folders/[id]/+page';

describe('folders/[id] load', () => {
	beforeEach(() => {
		folderGetMock.mockReset();
		channelsListMock.mockReset();
		videosListMock.mockReset();
		createScopedAPIMock.mockReset();
		parseVideoFilterQueryMock.mockReset();
		errorMock.mockClear();

		createScopedAPIMock.mockReturnValue({
			folders: { get: folderGetMock },
			channels: { list: channelsListMock },
			videos: { list: videosListMock }
		});
		parseVideoFilterQueryMock.mockReturnValue({ apiFilters: {}, uiFilters: {} });
	});

	it('throws 404 only when the backend reports that the folder is missing', async () => {
		folderGetMock.mockRejectedValue(new APIErrorMock(404));
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);

		await expect(
			load({
				params: { id: 'missing' },
				url: new URL('http://localhost/folders/missing'),
				fetch: vi.fn(),
				parent: vi.fn()
			} as any)
		).rejects.toMatchObject({ status: 404, message: 'Folder not found' });

		expect(errorMock).toHaveBeenCalledWith(404, 'Folder not found');
		consoleErrorSpy.mockRestore();
	});

	it('reports video transport failures as a bad gateway instead of a false 404', async () => {
		folderGetMock.mockResolvedValue({ id: 'folder-1', name: 'Folder' });
		channelsListMock.mockResolvedValue({ items: [{ id: 'channel-1' }], total: 1 });
		videosListMock.mockRejectedValue(new TypeError('Decoding failed'));
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);

		await expect(
			load({
				params: { id: 'folder-1' },
				url: new URL('http://localhost/folders/folder-1'),
				fetch: vi.fn(),
				parent: vi.fn()
			} as any)
		).rejects.toMatchObject({
			status: 502,
			message: 'Folder videos could not be loaded. Please retry.'
		});

		expect(errorMock).toHaveBeenCalledWith(502, 'Folder videos could not be loaded. Please retry.');
		consoleErrorSpy.mockRestore();
	});
});
