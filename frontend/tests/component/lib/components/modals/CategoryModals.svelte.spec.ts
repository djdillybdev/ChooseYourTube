import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import type { CategoryOut } from '../../../../../src/lib/types/api';

const { createMock, updateMock, setChannelsMock, invalidateMock } = vi.hoisted(() => ({
	createMock: vi.fn(),
	updateMock: vi.fn(),
	setChannelsMock: vi.fn(),
	invalidateMock: vi.fn()
}));

vi.mock('$lib/api', () => ({
	api: {
		categories: {
			create: createMock,
			update: updateMock,
			setChannels: setChannelsMock,
			delete: vi.fn()
		}
	}
}));

vi.mock('$app/navigation', () => ({
	goto: vi.fn(),
	invalidate: invalidateMock
}));

vi.mock('$app/state', () => ({ page: { url: new URL('http://localhost/inbox') } }));

import CreateCategoryModal from '../../../../../src/lib/components/modals/CreateCategoryModal.svelte';
import EditCategoryModal from '../../../../../src/lib/components/modals/EditCategoryModal.svelte';

beforeAll(() => {
	HTMLDialogElement.prototype.showModal = function () {
		this.open = true;
	};
});

beforeEach(() => {
	createMock.mockReset().mockResolvedValue({});
	updateMock.mockReset().mockResolvedValue({});
	setChannelsMock.mockReset().mockResolvedValue({});
	invalidateMock.mockReset().mockResolvedValue(undefined);
});

function makeCategory(overrides: Partial<CategoryOut> = {}): CategoryOut {
	return {
		id: 'category-a',
		name: 'Games',
		icon_key: 'gamepad-2',
		created_at: '2026-01-01T00:00:00Z',
		channel_ids: [],
		...overrides
	};
}

describe('category modals', () => {
	it('submits the selected icon when creating a category', async () => {
		render(CreateCategoryModal, { onClose: vi.fn() });

		await fireEvent.input(screen.getByLabelText('Category Name'), {
			target: { value: 'Games' }
		});
		await fireEvent.click(screen.getByRole('radio', { name: 'Gaming' }));
		await fireEvent.click(screen.getByRole('button', { name: 'Create Category' }));

		await waitFor(() =>
			expect(createMock).toHaveBeenCalledWith({ name: 'Games', icon_key: 'gamepad-2' })
		);
	});

	it('initializes and clears the icon when editing a category', async () => {
		render(EditCategoryModal, {
			category: makeCategory(),
			channels: [],
			onClose: vi.fn()
		});

		expect(screen.getByRole('radio', { name: 'Gaming' })).toHaveAttribute('aria-checked', 'true');
		await fireEvent.click(screen.getByRole('radio', { name: 'Default icon' }));
		await fireEvent.click(screen.getByRole('button', { name: 'Save' }));

		await waitFor(() =>
			expect(updateMock).toHaveBeenCalledWith('category-a', {
				name: 'Games',
				icon_key: null
			})
		);
	});
});
