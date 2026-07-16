import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Sidebar from '../../../../../src/lib/components/layout/Sidebar.svelte';
import type { ChannelOut } from '../../../../../src/lib/types/api';

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
		tag_ids: [],
		total_videos: 10,
		...overrides
	};
}

async function expand(name: string) {
	const button = screen.getByRole('button', { name: new RegExp(`(expand|collapse) ${name}`, 'i') });
	if (button.getAttribute('aria-label')?.startsWith('Expand')) await button.click();
}

describe('Sidebar', () => {
	it('shows channel thumbnail for unfoldered channels and keeps fallback icon when missing', async () => {
		render(Sidebar, {
			categories: [],
			uncategorizedChannels: [
				makeChannel({
					id: 'ch-thumb',
					title: 'Thumb Channel',
					thumbnail_url: 'https://img.example/thumb.jpg'
				}),
				makeChannel({ id: 'ch-no-thumb', title: 'No Thumb Channel', thumbnail_url: null })
			],
			channels: []
		});
		await expand('uncategorized');

		const thumbnail = screen.getByAltText('Thumb Channel');
		expect(thumbnail).toHaveAttribute('src', 'https://img.example/thumb.jpg');

		const noThumbLink = document.querySelector('a[href="/channels/ch-no-thumb"]');
		expect(noThumbLink).toBeInTheDocument();
		expect(noThumbLink?.querySelector('img')).not.toBeInTheDocument();
		expect(noThumbLink?.querySelector('svg')).toBeInTheDocument();
	});

	it('renders edit channel action without requiring mouse hover', async () => {
		render(Sidebar, {
			categories: [],
			uncategorizedChannels: [makeChannel({ id: 'ch-edit', title: 'Editable Channel' })],
			channels: []
		});
		await expand('uncategorized');

		expect(screen.getByRole('button', { name: /edit editable channel/i })).toBeInTheDocument();
	});

	it('renders favorites directly below inbox and before other library links', async () => {
		render(Sidebar, {
			categories: [],
			uncategorizedChannels: [],
			channels: []
		});

		const links = screen.getAllByRole('link');
		const inboxIndex = links.findIndex((link) => link.textContent?.includes('Inbox'));
		const favoritesIndex = links.findIndex((link) => link.textContent?.includes('Favorites'));
		const playlistsIndex = links.findIndex((link) => link.textContent?.includes('Playlists'));

		expect(screen.getByRole('link', { name: /favorites/i })).toHaveAttribute('href', '/favorites');
		expect(favoritesIndex).toBe(inboxIndex + 1);
		expect(playlistsIndex).toBeGreaterThan(favoritesIndex);
		expect(screen.getByRole('link', { name: /playlists/i })).toHaveAttribute('href', '/playlists');
	});

	it('shows a channel in every assigned category and only zero-category channels as uncategorized', async () => {
		const shared = makeChannel({ id: 'shared', title: 'Shared Channel' });
		const loose = makeChannel({ id: 'loose', title: 'Loose Channel' });
		render(Sidebar, {
			categories: [
				{ id: 'games', name: 'Games', created_at: '2026-01-01T00:00:00Z', channel_ids: ['shared'] },
				{ id: 'tech', name: 'Tech', created_at: '2026-01-01T00:00:00Z', channel_ids: ['shared'] }
			],
			uncategorizedChannels: [loose],
			channels: [shared, loose]
		});

		await expand('games');
		await expand('tech');
		await expand('uncategorized');
		expect(screen.getAllByText('Shared Channel')).toHaveLength(2);
		expect(screen.getAllByText('Loose Channel')).toHaveLength(1);
	});

	it('renders selected category icons and falls back for missing icons', () => {
		render(Sidebar, {
			categories: [
				{
					id: 'games',
					name: 'Games',
					icon_key: 'gamepad-2',
					created_at: '2026-01-01T00:00:00Z',
					channel_ids: []
				},
				{
					id: 'other',
					name: 'Other',
					icon_key: 'removed-icon',
					created_at: '2026-01-01T00:00:00Z',
					channel_ids: []
				}
			],
			uncategorizedChannels: [],
			channels: []
		});

		expect(
			screen.getByRole('link', { name: 'Games' }).querySelector('.lucide-gamepad-2')
		).toBeTruthy();
		expect(screen.getByRole('link', { name: 'Other' }).querySelector('.lucide-list')).toBeTruthy();
	});
});
