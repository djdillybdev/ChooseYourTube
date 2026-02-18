import { describe, expect, it } from 'vitest';
import { createChannelMap, getChannelTitle } from '../../../../src/lib/utils/channelLookup';

describe('channelLookup utils', () => {
	it('creates a map keyed by channel id', () => {
		const map = createChannelMap([
			{ id: 'ch-1', title: 'Channel One' },
			{ id: 'ch-2', title: 'Channel Two' }
		] as any);

		expect(map.get('ch-1')?.title).toBe('Channel One');
		expect(map.get('ch-2')?.title).toBe('Channel Two');
	});

	it('returns channel title with fallback when missing', () => {
		const map = createChannelMap([{ id: 'abcdefghi', title: 'Known' }] as any);

		expect(getChannelTitle('abcdefghi', map)).toBe('Known');
		expect(getChannelTitle('1234567890xyz', map)).toBe('Channel 12345678...');
	});
});
