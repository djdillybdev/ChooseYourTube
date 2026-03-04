import { fireEvent, render, screen } from '@testing-library/svelte';
import { beforeAll, describe, expect, it, vi } from 'vitest';
import EditChannelModal from '../../../../../src/lib/components/modals/EditChannelModal.svelte';
import type { ChannelOut, FolderOut } from '../../../../../src/lib/types/api';

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
		total_videos: 10,
		...overrides
	};
}

function makeFolder(overrides: Partial<FolderOut>): FolderOut {
	return {
		id: 'folder-a',
		name: 'Folder A',
		parent_id: null,
		position: 0,
		children: [],
		...overrides
	};
}

describe('EditChannelModal', () => {
	it('resets local form state when channel prop changes', async () => {
		const folders = [makeFolder({ id: 'folder-a' }), makeFolder({ id: 'folder-b', name: 'Folder B' })];
		const first = makeChannel({ id: 'ch-1', is_favorited: false, folder_id: 'folder-a' });
		const second = makeChannel({ id: 'ch-2', is_favorited: false, folder_id: 'folder-a' });

		const { rerender } = render(EditChannelModal, {
			channel: first,
			folders,
			onClose: vi.fn()
		});

		const favoriteToggle = screen.getByRole('checkbox', { hidden: true }) as HTMLInputElement;
		const folderSelect = screen.getByLabelText('Folder') as HTMLSelectElement;

		expect(favoriteToggle.checked).toBe(false);
		expect(folderSelect.value).toBe('folder-a');

		await fireEvent.click(favoriteToggle);
		await fireEvent.change(folderSelect, { target: { value: 'folder-b' } });
		expect(favoriteToggle.checked).toBe(true);
		expect(folderSelect.value).toBe('folder-b');

		await rerender({ channel: second, folders, onClose: vi.fn() });

		expect(favoriteToggle.checked).toBe(false);
		expect(folderSelect.value).toBe('folder-a');
	});
});
