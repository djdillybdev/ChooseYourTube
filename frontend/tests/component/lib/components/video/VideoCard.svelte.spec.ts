import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import VideoCard from '../../../../../src/lib/components/video/VideoCard.svelte';
import type { VideoOut } from '../../../../../src/lib/types/api';

function makeVideo(overrides: Partial<VideoOut> = {}): VideoOut {
	return {
		id: 'video-1',
		channel_id: 'channel-1',
		title: 'A video',
		description: null,
		thumbnail_url: null,
		published_at: '2026-01-01T00:00:00Z',
		created_at: '2026-01-01T00:00:00Z',
		duration_seconds: 120,
		is_watched: false,
		is_favorited: true,
		is_short: false,
		tag_ids: [],
		yt_tags: [],
		...overrides
	};
}

describe('VideoCard', () => {
	it('renders playback and watched actions without requiring hover', async () => {
		render(VideoCard, { video: makeVideo() });

		expect(screen.queryByRole('button', { name: /favorites/i })).not.toBeInTheDocument();
		expect(screen.getAllByRole('button', { name: 'Play A video' }).length).toBeGreaterThan(0);
		expect(screen.getByRole('button', { name: 'Mark as watched' })).toBeInTheDocument();
	});

	it('uses the provided queue-aware playback callback', async () => {
		const onPlay = vi.fn().mockResolvedValue(false);
		render(VideoCard, { video: makeVideo(), onPlay });

		await fireEvent.click(screen.getAllByRole('button', { name: 'Play A video' })[0]);

		expect(onPlay).toHaveBeenCalledOnce();
		expect(onPlay).toHaveBeenCalledWith(expect.objectContaining({ id: 'video-1' }));
	});

	it('closes the more-actions menu after selecting an action', async () => {
		render(VideoCard, { video: makeVideo() });
		const details = screen.getByText('More').closest('details');
		expect(details).not.toBeNull();
		details!.open = true;

		await fireEvent.click(screen.getByRole('button', { name: 'Save to playlist' }));

		expect(details).not.toHaveAttribute('open');
	});

	it('renders the thumbnail in grid mode', () => {
		render(VideoCard, {
			video: makeVideo({ thumbnail_url: 'https://img.example/video.jpg' }),
			displayMode: 'grid'
		});

		expect(screen.getByRole('article', { name: 'A video' })).toHaveAttribute(
			'data-display-mode',
			'grid'
		);
		expect(document.querySelector('img')).toHaveAttribute('src', 'https://img.example/video.jpg');
	});

	it('omits all thumbnail markup in compact mode while retaining actions', () => {
		render(VideoCard, {
			video: makeVideo({ thumbnail_url: 'https://img.example/video.jpg' }),
			displayMode: 'compact'
		});

		expect(screen.getByRole('article', { name: 'A video' })).toHaveAttribute(
			'data-display-mode',
			'compact'
		);
		expect(document.querySelector('img')).not.toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Play A video' })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Mark as watched' })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Save to Watch Later' })).toBeInTheDocument();
	});
});
