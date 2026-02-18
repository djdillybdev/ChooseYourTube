import { fireEvent, render, screen } from '@testing-library/svelte';
import { beforeAll, describe, expect, it, vi } from 'vitest';
import EditFolderModal from '../../../../../src/lib/components/modals/EditFolderModal.svelte';
import type { FolderOut } from '../../../../../src/lib/types/api';

beforeAll(() => {
	if (!HTMLDialogElement.prototype.showModal) {
		HTMLDialogElement.prototype.showModal = vi.fn();
	}
});

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

describe('EditFolderModal', () => {
	it('resets local form state when folder prop changes', async () => {
		const folders = [
			makeFolder({ id: 'folder-a', name: 'Folder A' }),
			makeFolder({ id: 'folder-b', name: 'Folder B' }),
			makeFolder({ id: 'folder-c', name: 'Folder C' })
		];
		const first = makeFolder({ id: 'folder-a', name: 'Folder A', parent_id: null });
		const second = makeFolder({ id: 'folder-b', name: 'Folder B', parent_id: null });

		const { rerender } = render(EditFolderModal, {
			folder: first,
			folders,
			onClose: vi.fn()
		});

		const nameInput = screen.getByLabelText('Name') as HTMLInputElement;
		const parentSelect = screen.getByLabelText('Parent Folder') as HTMLSelectElement;

		expect(nameInput.value).toBe('Folder A');
		expect(parentSelect.value).toBe('');

		await fireEvent.input(nameInput, { target: { value: 'Modified Name' } });
		await fireEvent.change(parentSelect, { target: { value: 'folder-c' } });
		expect(nameInput.value).toBe('Modified Name');
		expect(parentSelect.value).toBe('folder-c');

		await rerender({ folder: second, folders, onClose: vi.fn() });

		expect(nameInput.value).toBe('Folder B');
		expect(parentSelect.value).toBe('');
	});
});
