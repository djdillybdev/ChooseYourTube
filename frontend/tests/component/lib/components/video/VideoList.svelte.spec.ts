import { fireEvent, render, screen } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import VideoList from '../../../../../src/lib/components/video/VideoList.svelte';
import { setVideoDisplayMode, uiState } from '../../../../../src/lib/stores/uiState.svelte';
import type { VideoOut } from '../../../../../src/lib/types/api';

function makeVideo(id: string): VideoOut {
	return {
		id,
		channel_id: 'channel-1',
		title: `Video ${id}`,
		description: null,
		thumbnail_url: `https://img.example/${id}.jpg`,
		published_at: '2026-01-01T00:00:00Z',
		created_at: '2026-01-01T00:00:00Z',
		duration_seconds: 120,
		is_watched: false,
		is_favorited: false,
		is_short: false,
		tag_ids: [],
		yt_tags: []
	};
}

describe('VideoList', () => {
	beforeEach(() => {
		const values = new Map<string, string>();
		vi.stubGlobal('localStorage', {
			getItem: (key: string) => values.get(key) ?? null,
			setItem: (key: string, value: string) => values.set(key, value),
			removeItem: (key: string) => values.delete(key),
			clear: () => values.clear()
		});
		setVideoDisplayMode('list');
	});

	afterEach(() => vi.unstubAllGlobals());

	it('defaults to the list layout with an accessible display selector', () => {
		render(VideoList, { videos: [makeVideo('1')] });

		expect(screen.getByRole('group', { name: 'Video display' })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'List view' })).toHaveAttribute(
			'aria-pressed',
			'true'
		);
		expect(screen.getByTestId('video-items')).toHaveAttribute('data-display-mode', 'list');
		expect(screen.getByTestId('video-items')).toHaveStyle('--video-grid-columns: 4');
	});

	it('switches layouts and persists one global preference', async () => {
		render(VideoList, { videos: [makeVideo('1'), makeVideo('2')] });

		await fireEvent.click(screen.getByRole('button', { name: 'Grid view' }));

		expect(screen.getByRole('button', { name: 'Grid view' })).toHaveAttribute(
			'aria-pressed',
			'true'
		);
		expect(screen.getByTestId('video-items')).toHaveAttribute('data-display-mode', 'grid');
		expect(uiState.current.videoDisplayMode).toBe('grid');
		expect(JSON.parse(localStorage.getItem('cyt:ui') ?? '{}')).toMatchObject({
			videoDisplayMode: 'grid'
		});

		await fireEvent.click(screen.getByRole('button', { name: 'Compact view' }));
		expect(screen.getByTestId('video-items')).toHaveAttribute('data-display-mode', 'compact');
		expect(document.querySelector('img')).not.toBeInTheDocument();
	});

	it('accepts a configurable desktop grid column count', async () => {
		render(VideoList, { videos: [makeVideo('1')], gridColumns: 5 });

		await fireEvent.click(screen.getByRole('button', { name: 'Grid view' }));

		expect(screen.getByTestId('video-items')).toHaveStyle('--video-grid-columns: 5');
	});
});
