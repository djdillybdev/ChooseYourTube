import { beforeEach, describe, expect, it, vi } from 'vitest';

const { errorMock, redirectMock } = vi.hoisted(() => ({
	errorMock: vi.fn((status: number, message: string) => {
		const failure = new Error(message) as Error & { status: number };
		failure.status = status;
		throw failure;
	}),
	redirectMock: vi.fn((status: number, location: string) => {
		const failure = new Error('redirect') as Error & { status: number; location: string };
		failure.status = status;
		failure.location = location;
		throw failure;
	})
}));

vi.mock('@sveltejs/kit', () => ({
	error: errorMock,
	redirect: redirectMock
}));

import { load } from '../../../src/routes/+layout';

describe('root layout load', () => {
	beforeEach(() => {
		errorMock.mockClear();
		redirectMock.mockClear();
	});

	it('skips the bootstrap request for public authentication routes', async () => {
		const fetchMock = vi.fn();
		const result = await load({
			depends: vi.fn(),
			fetch: fetchMock,
			url: new URL('http://localhost/login')
		} as any);

		expect(fetchMock).not.toHaveBeenCalled();
		expect(result).toMatchObject({ isPublicAuthRoute: true, currentUser: null });
	});

	it('maps a successful bootstrap payload into layout data', async () => {
		const payload = {
			current_user: { id: 'user-1', email: 'demo@example.com' },
			folders: [{ id: 'folder-1', name: 'News' }],
			channels: [
				{ id: 'channel-1', title: 'One', folder_id: null },
				{ id: 'channel-2', title: 'Two', folder_id: 'folder-1' }
			],
			tags: [{ id: 'tag-1', name: 'science' }],
			watch_later: { id: 'watch-later', video_ids: [] },
			runtime: { name: 'ChooseYourTube', version: '0.1.0', mode: 'demo', features: {} }
		};
		const categories = [
			{
				id: 'category-1',
				name: 'News',
				created_at: '2026-01-01T00:00:00Z',
				channel_ids: ['channel-2']
			}
		];
		const fetchMock = vi
			.fn()
			.mockResolvedValueOnce(Response.json(payload))
			.mockResolvedValueOnce(Response.json(categories));

		const result = await load({
			depends: vi.fn(),
			fetch: fetchMock,
			url: new URL('http://localhost/inbox')
		} as any);

		expect(fetchMock).toHaveBeenCalledWith('/api/bootstrap');
		expect(result).toMatchObject({
			currentUser: payload.current_user,
			channels: payload.channels,
			categories,
			uncategorizedChannels: [payload.channels[0]],
			watchLater: payload.watch_later
		});
	});

	it('logs out and redirects when bootstrap remains unauthorized', async () => {
		const fetchMock = vi
			.fn()
			.mockResolvedValueOnce(new Response(null, { status: 401 }))
			.mockResolvedValueOnce(new Response(null, { status: 204 }));

		await expect(
			load({
				depends: vi.fn(),
				fetch: fetchMock,
				url: new URL('http://localhost/inbox?page=2')
			} as any)
		).rejects.toMatchObject({
			status: 307,
			location: '/login?reason=session_expired&next=%2Finbox%3Fpage%3D2'
		});
		expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/auth/logout', { method: 'POST' });
	});

	it('surfaces bootstrap failures instead of rendering an empty library', async () => {
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 500 }));

		await expect(
			load({
				depends: vi.fn(),
				fetch: fetchMock,
				url: new URL('http://localhost/inbox')
			} as any)
		).rejects.toMatchObject({
			status: 503,
			message: 'ChooseYourTube could not load your library. Please retry.'
		});

		consoleErrorSpy.mockRestore();
	});
});
