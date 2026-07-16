import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { updateMock, invalidateMock } = vi.hoisted(() => ({
	updateMock: vi.fn(),
	invalidateMock: vi.fn()
}));

vi.mock('$lib/api', () => ({
	api: { channels: { update: updateMock } }
}));

vi.mock('$app/navigation', () => ({ invalidate: invalidateMock }));

import ChannelFavoriteButton from '../../../../../src/lib/components/channel/ChannelFavoriteButton.svelte';

describe('ChannelFavoriteButton', () => {
	beforeEach(() => {
		updateMock.mockReset();
		invalidateMock.mockReset();
	});

	it('favorites a channel and refreshes channel-backed views', async () => {
		updateMock.mockResolvedValue({ id: 'channel-1', is_favorited: true });
		invalidateMock.mockResolvedValue(undefined);
		render(ChannelFavoriteButton, {
			channelId: 'channel-1',
			channelTitle: 'Channel One',
			isFavorited: false
		});

		await fireEvent.click(screen.getByRole('button', { name: 'Add Channel One to favorites' }));

		expect(updateMock).toHaveBeenCalledWith('channel-1', { is_favorited: true });
		await waitFor(() => expect(invalidateMock).toHaveBeenCalledWith('app:channels'));
		expect(
			screen.getByRole('button', { name: 'Remove Channel One from favorites' })
		).toBeInTheDocument();
	});

	it('keeps the prior state and exposes an error when the update fails', async () => {
		updateMock.mockRejectedValue(new Error('offline'));
		render(ChannelFavoriteButton, {
			channelId: 'channel-1',
			channelTitle: 'Channel One',
			isFavorited: false
		});

		await fireEvent.click(screen.getByRole('button', { name: 'Add Channel One to favorites' }));

		await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('offline'));
		expect(
			screen.getByRole('button', { name: 'Add Channel One to favorites' })
		).toBeInTheDocument();
		expect(invalidateMock).not.toHaveBeenCalled();
	});
});
