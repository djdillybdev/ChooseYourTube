import { render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Sidebar from '../../../../../src/lib/components/layout/Sidebar.svelte';
import type { ChannelOut } from '../../../../../src/lib/types/api';

const { listMock } = vi.hoisted(() => ({
	listMock: vi.fn()
}));

vi.mock('$lib/api', () => ({
	api: {
		channels: {
			list: listMock
		}
	}
}));

function makeChannel(overrides: Partial<ChannelOut>): ChannelOut {
	return {
		id: 'ch-1',
		title: 'Channel 1',
		handle: '@channel1',
		description: null,
		thumbnail_url: null,
		is_favorited: false,
		folder_id: null,
		created_at: '2026-01-01T00:00:00Z',
		last_updated: '2026-01-01T00:00:00Z',
		total_videos: 10,
		...overrides
	};
}

describe('Sidebar', () => {
	beforeEach(() => {
		listMock.mockReset();
		listMock.mockResolvedValue({
			items: [],
			total: 0,
			limit: 50,
			offset: 0,
			has_more: false
		});
	});

	it('shows channel thumbnail for unfoldered channels and keeps fallback icon when missing', async () => {
		render(Sidebar, {
			folders: [],
			unfolderedChannels: [
				makeChannel({ id: 'ch-thumb', title: 'Thumb Channel', thumbnail_url: 'https://img.example/thumb.jpg' }),
				makeChannel({ id: 'ch-no-thumb', title: 'No Thumb Channel', thumbnail_url: null })
			]
		});

		await waitFor(() => {
			expect(listMock).toHaveBeenCalled();
		});

		const thumbnail = screen.getByAltText('Thumb Channel');
		expect(thumbnail).toHaveAttribute('src', 'https://img.example/thumb.jpg');

		const noThumbLink = document.querySelector('a[href="/channels/ch-no-thumb"]');
		expect(noThumbLink).toBeInTheDocument();
		expect(noThumbLink?.querySelector('img')).not.toBeInTheDocument();
		expect(noThumbLink?.querySelector('svg')).toBeInTheDocument();
	});

	it('renders edit channel action without requiring mouse hover', async () => {
		render(Sidebar, {
			folders: [],
			unfolderedChannels: [makeChannel({ id: 'ch-edit', title: 'Editable Channel' })]
		});

		await waitFor(() => {
			expect(listMock).toHaveBeenCalled();
		});

		expect(screen.getByRole('button', { name: /edit channel/i })).toBeInTheDocument();
	});

	it('renders playlists navigation link below inbox', async () => {
		render(Sidebar, {
			folders: [],
			unfolderedChannels: []
		});

		await waitFor(() => {
			expect(listMock).toHaveBeenCalled();
		});

		expect(screen.getByRole('link', { name: /inbox/i })).toBeInTheDocument();
		expect(screen.getByRole('link', { name: /playlists/i })).toHaveAttribute('href', '/playlists');
	});
});
