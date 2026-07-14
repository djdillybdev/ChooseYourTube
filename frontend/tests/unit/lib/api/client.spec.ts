import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { APIError } from '../../../../src/lib/types/api';
import { APIClient } from '../../../../src/lib/api/client';
import { server } from '../../../msw/server';

describe('APIClient', () => {
	beforeEach(() => {
		vi.useFakeTimers();
	});

	afterEach(() => {
		vi.useRealTimers();
		delete (globalThis as { window?: unknown }).window;
	});

	it('retries on server errors and eventually succeeds', async () => {
		let attempts = 0;
		server.use(
			http.get('http://api.test/videos', () => {
				attempts += 1;
				if (attempts < 3) {
					return HttpResponse.json({ detail: 'oops' }, { status: 503 });
				}
				return HttpResponse.json({ items: [] });
			})
		);

		const client = new APIClient('http://api.test');
		const request = client.fetch<{ items: unknown[] }>('/videos', { retries: 3 });
		await vi.runAllTimersAsync();
		const data = await request;

		expect(attempts).toBe(3);
		expect(data).toEqual({ items: [] });
	});

	it('does not retry on 4xx API errors', async () => {
		let attempts = 0;
		server.use(
			http.get('http://api.test/channels', () => {
				attempts += 1;
				return HttpResponse.json({ detail: 'bad request' }, { status: 400 });
			})
		);

		const client = new APIClient('http://api.test');

		await expect(client.fetch('/channels', { retries: 3 })).rejects.toBeInstanceOf(APIError);
		expect(attempts).toBe(1);
	});

	it('extracts the stable API error contract', async () => {
		server.use(
			http.get('http://api.test/channels', () =>
				HttpResponse.json(
					{
						code: 'FEATURE_DISABLED',
						message: 'Safe backend message',
						request_id: 'request-123',
						retryable: false
					},
					{ status: 403 }
				)
			)
		);

		const client = new APIClient('http://api.test');
		const error = await client.get('/channels').catch((caught) => caught);

		expect(error).toBeInstanceOf(APIError);
		expect(error).toMatchObject({
			code: 'FEATURE_DISABLED',
			requestId: 'request-123',
			retryable: false
		});
		expect((error as APIError).message).toContain('Request ID: request-123');
	});

	it('builds filtered query params for get requests', async () => {
		server.use(
			http.get('http://api.test/videos', ({ request }) => {
				const url = new URL(request.url);
				expect(url.searchParams.get('page')).toBe('2');
				expect(url.searchParams.get('q')).toBe('svelte');
				expect(url.searchParams.get('unused')).toBeNull();
				return HttpResponse.json({ ok: true });
			})
		);

		const client = new APIClient('http://api.test');
		const data = await client.get('/videos', {
			page: 2,
			q: 'svelte',
			unused: undefined,
			nothing: null
		});

		expect(data).toEqual({ ok: true });
	});

	it('caches successful get responses in browser-like environment', async () => {
		(globalThis as { window?: unknown }).window = {};
		let attempts = 0;
		server.use(
			http.get('http://api.test/tags', () => {
				attempts += 1;
				return HttpResponse.json({ items: [{ id: String(attempts) }] });
			})
		);

		const client = new APIClient('http://api.test');

		const first = await client.fetch('/tags', { method: 'GET', cacheTTL: 60_000 });
		const second = await client.fetch('/tags', { method: 'GET', cacheTTL: 60_000 });

		expect(first).toEqual({ items: [{ id: '1' }] });
		expect(second).toEqual({ items: [{ id: '1' }] });
		expect(attempts).toBe(1);
	});
});
