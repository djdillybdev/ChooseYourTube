import { fireEvent, render, screen } from '@testing-library/svelte';
import { beforeAll, describe, expect, it, vi } from 'vitest';
import EditChannelModal from '../../../../../src/lib/components/modals/EditChannelModal.svelte';
import type { CategoryOut, ChannelOut } from '../../../../../src/lib/types/api';

beforeAll(() => {
	if (!HTMLDialogElement.prototype.showModal) {
		HTMLDialogElement.prototype.showModal = vi.fn();
	}
});

function makeChannel(overrides: Partial<ChannelOut>): ChannelOut {
	return {
		id: 'ch-1',
		title: 'Channel One',
		handle: '@channelone',
		description: null,
		thumbnail_url: null,
		is_favorited: false,
		folder_id: 'folder-a',
		created_at: '2026-01-01T00:00:00Z',
		last_updated: '2026-01-01T00:00:00Z',
		tag_ids: [],
		total_videos: 10,
		...overrides
	};
}

function makeCategory(overrides: Partial<CategoryOut>): CategoryOut {
	return {
		id: 'category-a',
		name: 'Category A',
		created_at: '2026-01-01T00:00:00Z',
		channel_ids: [],
		...overrides
	};
}

describe('EditChannelModal', () => {
	it('resets local form state when channel prop changes', async () => {
		const categories = [
			makeCategory({ id: 'category-a', channel_ids: ['ch-1', 'ch-2'] }),
			makeCategory({ id: 'category-b', name: 'Category B', channel_ids: [] })
		];
		const first = makeChannel({ id: 'ch-1', is_favorited: false, folder_id: 'folder-a' });
		const second = makeChannel({ id: 'ch-2', is_favorited: false, folder_id: 'folder-a' });

		const { rerender } = render(EditChannelModal, {
			channel: first,
			categories,
			onClose: vi.fn()
		});

		const favoriteToggle = screen.getAllByRole('checkbox', { hidden: true })[0] as HTMLInputElement;
		const categoryA = screen.getByLabelText('Category A') as HTMLInputElement;
		const categoryB = screen.getByLabelText('Category B') as HTMLInputElement;

		expect(favoriteToggle.checked).toBe(false);
		expect(categoryA.checked).toBe(true);
		expect(categoryB.checked).toBe(false);

		await fireEvent.click(favoriteToggle);
		await fireEvent.click(categoryB);
		expect(favoriteToggle.checked).toBe(true);
		expect(categoryB.checked).toBe(true);

		await rerender({ channel: second, categories, onClose: vi.fn() });

		expect(favoriteToggle.checked).toBe(false);
		expect(categoryA.checked).toBe(true);
		expect(categoryB.checked).toBe(false);
	});
});
