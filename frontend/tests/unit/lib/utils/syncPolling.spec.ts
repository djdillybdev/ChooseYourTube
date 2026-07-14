import { describe, expect, it, vi } from 'vitest';
import { isTerminalSync, pollSyncRun } from '$lib/utils/syncPolling';
import type { SyncRunOut } from '$lib/types/api';

function run(status: SyncRunOut['status']): SyncRunOut {
	return {
		id: '00000000-0000-0000-0000-000000000001',
		owner_id: 'owner',
		kind: 'channel_refresh',
		status,
		channel_id: 'channel',
		subscription_import_id: null,
		attempt_count: 1,
		max_attempts: 4,
		items_discovered: 0,
		items_created: 0,
		items_updated: 0,
		items_skipped: 0,
		items_failed: 0,
		error_code: null,
		error_message: null,
		retryable: false,
		queued_at: '2026-07-14T00:00:00Z',
		started_at: null,
		finished_at: null,
		next_retry_at: null,
		created_at: '2026-07-14T00:00:00Z',
		updated_at: '2026-07-14T00:00:00Z'
	};
}

describe('sync polling', () => {
	it('polls until a terminal state and reports transitions', async () => {
		const getRun = vi
			.fn()
			.mockResolvedValueOnce(run('queued'))
			.mockResolvedValueOnce(run('running'))
			.mockResolvedValueOnce(run('succeeded'));
		const update = vi.fn();
		const result = await pollSyncRun('id', getRun, update, () => false, vi.fn());
		expect(result?.status).toBe('succeeded');
		expect(update.mock.calls.map(([value]) => value.status)).toEqual([
			'queued',
			'running',
			'succeeded'
		]);
	});

	it('stops without another request after cancellation', async () => {
		let cancelled = false;
		const getRun = vi.fn().mockResolvedValue(run('queued'));
		const result = await pollSyncRun(
			'id',
			getRun,
			() => (cancelled = true),
			() => cancelled,
			vi.fn()
		);
		expect(result).toBeNull();
		expect(getRun).toHaveBeenCalledOnce();
	});

	it('recognizes all terminal states', () => {
		expect(
			['succeeded', 'partial', 'failed'].every((status) => isTerminalSync(status as never))
		).toBe(true);
		expect(isTerminalSync('running')).toBe(false);
	});
});
