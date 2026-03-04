import { describe, expect, it } from 'vitest';
import { formatDuration } from '../../src/lib/utils/formatDuration';

describe('formatDuration', () => {
	it('formats minute-second durations', () => {
		expect(formatDuration(83)).toBe('1:23');
	});

	it('formats hour-minute-second durations', () => {
		expect(formatDuration(5025)).toBe('1:23:45');
	});

	it('returns 0:00 for nullish or negative durations', () => {
		expect(formatDuration(null)).toBe('0:00');
		expect(formatDuration(undefined)).toBe('0:00');
		expect(formatDuration(-1)).toBe('0:00');
	});
});
