import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
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
	it('does not offer video favorite actions', async () => {
		render(VideoCard, { video: makeVideo() });

		await fireEvent.mouseEnter(screen.getByRole('group', { name: 'A video' }));

		expect(screen.queryByRole('button', { name: /favorites/i })).not.toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Mark as watched' })).toBeInTheDocument();
	});
});
