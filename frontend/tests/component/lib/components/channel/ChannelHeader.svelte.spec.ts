import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import ChannelHeader from '../../../../../src/lib/components/channel/ChannelHeader.svelte';
import type { ChannelOut, SyncRunOut } from '../../../../../src/lib/types/api';

const longTitle = 'A deliberately long channel title '.repeat(4).trim();
const channel: ChannelOut = {
	id: 'channel-1',
	title: longTitle,
	handle: 'long-channel',
	description: null,
	thumbnail_url: null,
	is_favorited: false,
	folder_id: null,
	created_at: '2026-01-01T00:00:00Z',
	last_updated: '2026-01-01T00:00:00Z',
	total_videos: 0,
	latest_sync: null,
	tag_ids: []
};

const failedSync = {
	id: '00000000-0000-0000-0000-000000000001',
	owner_id: 'user-1',
	kind: 'initial_channel_sync',
	status: 'failed',
	channel_id: channel.id,
	subscription_import_id: null,
	attempt_count: 1,
	max_attempts: 4,
	items_discovered: 0,
	items_created: 0,
	items_updated: 0,
	items_skipped: 0,
	items_failed: 0,
	error_code: 'QUEUE_UNAVAILABLE',
	error_message: 'Synchronization is temporarily unavailable.',
	retryable: true,
	queued_at: '2026-01-01T00:00:00Z',
	started_at: null,
	finished_at: '2026-01-01T00:00:01Z',
	next_retry_at: null,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:01Z'
} satisfies SyncRunOut;

describe('ChannelHeader', () => {
	it('keeps long and missing-avatar identity accessible and renders status in human language', () => {
		render(ChannelHeader, {
			channel,
			countLabel: '0 videos',
			sync: failedSync,
			onEdit: vi.fn(),
			onRefresh: vi.fn()
		});

		expect(screen.getByRole('heading', { level: 1, name: longTitle })).toBeVisible();
		expect(screen.getByText('Sync failed')).toBeVisible();
		expect(screen.queryByRole('img')).not.toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Edit channel' })).toBeVisible();
	});

	it('exposes only supported actions and invokes them once', async () => {
		const onEdit = vi.fn();
		const onRefresh = vi.fn();
		render(ChannelHeader, { channel, countLabel: '1 video', onEdit, onRefresh });

		await fireEvent.click(screen.getByRole('button', { name: 'Edit channel' }));
		await fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
		expect(onEdit).toHaveBeenCalledOnce();
		expect(onRefresh).toHaveBeenCalledOnce();
		expect(screen.queryByRole('button', { name: /favorites/i })).not.toBeInTheDocument();
	});
});
