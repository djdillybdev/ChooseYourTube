import { describe, expect, it } from 'vitest';
import { parseVideoFilterQuery } from '../../../../src/lib/utils/videoFilterQuery';

function parse(url: string, options?: Parameters<typeof parseVideoFilterQuery>[1]) {
	return parseVideoFilterQuery(new URL(url), options);
}

describe('parseVideoFilterQuery', () => {
	it('applies inbox watched default when is_watched is absent', () => {
		const result = parse('http://localhost/inbox', { defaultWatched: false });
		expect(result.apiFilters.is_watched).toBe(false);
		expect(result.uiFilters.is_watched).toBe(false);
	});

	it('parses boolean filters from query', () => {
		const result = parse('http://localhost/inbox?is_watched=true&is_favorited=false&is_short=true');
		expect(result.apiFilters.is_watched).toBe(true);
		expect(result.apiFilters.is_favorited).toBe(false);
		expect(result.apiFilters.is_short).toBe(true);
	});

	it('normalizes invalid sort fields and relevance without search', () => {
		const result = parse('http://localhost/inbox?order_by=relevance&order_direction=bad');
		expect(result.apiFilters.order_by).toBe('published_at');
		expect(result.apiFilters.order_direction).toBe('desc');
	});

	it('keeps relevance sorting when search query exists', () => {
		const result = parse('http://localhost/inbox?q=test');
		expect(result.apiFilters.order_by).toBe('relevance');
	});

	it('converts date filters to ISO day boundaries', () => {
		const result = parse(
			'http://localhost/inbox?published_after=2026-02-01&published_before=2026-02-15'
		);
		expect(result.apiFilters.published_after).toBe('2026-02-01T00:00:00.000Z');
		expect(result.apiFilters.published_before).toBe('2026-02-15T23:59:59.999Z');
	});

	it('enforces forcedChannelId over channel_id query', () => {
		const result = parse('http://localhost/channels/abc?channel_id=xyz', { forcedChannelId: 'abc' });
		expect(result.apiFilters.channel_id).toBe('abc');
	});
});
