import { describe, expect, it, vi } from 'vitest';
import { load } from '../../../../src/routes/settings/sync/+page';

const { list, quota } = vi.hoisted(() => ({
	list: vi.fn().mockResolvedValue({ total: 0, items: [], limit: 20, offset: 0, has_more: false }),
	quota: vi.fn().mockResolvedValue({
		date: '2026-07-14',
		budget: 8000,
		estimated_units_used: 0,
		estimated_units_remaining: 8000,
		call_count: 0,
		exhausted: false
	})
}));

vi.mock('$lib/api', () => ({
	createScopedAPI: () => ({ syncRuns: { list, quota } })
}));

describe('settings page load', () => {
	it('loads synchronization activity and quota status', async () => {
		const result = await load({
			fetch: vi.fn(),
			url: new URL('http://localhost/settings?status=failed')
		} as never);
		expect(list).toHaveBeenCalledWith({
			status: 'failed',
			kind: undefined,
			limit: 20,
			offset: 0
		});
		expect(result).toMatchObject({ page: 1, status: 'failed' });
	});
});
