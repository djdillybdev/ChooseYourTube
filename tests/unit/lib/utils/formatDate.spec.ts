import { beforeEach, describe, expect, it, vi } from 'vitest';
import { formatAbsoluteDate, formatRelativeDate } from '../../../../src/lib/utils/formatDate';

describe('formatDate utils', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2026-02-18T00:00:00.000Z'));
	});

	it('formats recent times as just now', () => {
		expect(formatRelativeDate('2026-02-17T23:59:45.000Z')).toBe('just now');
	});

	it('formats relative times across minute/hour/day buckets', () => {
		expect(formatRelativeDate('2026-02-17T23:58:00.000Z')).toBe('2 minutes ago');
		expect(formatRelativeDate('2026-02-17T22:00:00.000Z')).toBe('2 hours ago');
		expect(formatRelativeDate('2026-02-16T00:00:00.000Z')).toBe('2 days ago');
	});

	it('formats absolute dates in en-US short format', () => {
		expect(formatAbsoluteDate('2026-02-01T12:34:56.000Z')).toBe('Feb 1, 2026');
	});
});
