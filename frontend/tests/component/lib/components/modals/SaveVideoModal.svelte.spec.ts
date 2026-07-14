import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import SaveVideoModal from '../../../../../src/lib/components/modals/SaveVideoModal.svelte';
import type { PlaylistOut, VideoOut } from '../../../../../src/lib/types/api';

const { listMock, getMock, createMock, addVideoMock, removeVideoMock } = vi.hoisted(() => ({
	listMock: vi.fn(),
	getMock: vi.fn(),
	createMock: vi.fn(),
	addVideoMock: vi.fn(),
	removeVideoMock: vi.fn()
}));

vi.mock('$lib/api', () => ({
	api: {
		playlists: {
			list: listMock,
			get: getMock,
			create: createMock,
			addVideo: addVideoMock,
			removeVideo: removeVideoMock
		}
	}
}));

beforeAll(() => {
	if (!HTMLDialogElement.prototype.showModal) {
		HTMLDialogElement.prototype.showModal = vi.fn();
	}
});

function makePlaylist(overrides: Partial<PlaylistOut>): PlaylistOut {
	return {
		id: 'pl-1',
		name: 'Playlist 1',
		description: null,
		thumbnail_url: null,
		is_system: false,
		system_key: null,
		source_type: 'manual',
		source_channel_id: null,
		source_youtube_playlist_id: null,
		source_is_active: true,
		source_last_synced_at: null,
		created_at: '2026-01-01T00:00:00Z',
		...overrides
	};
}

function makeVideo(overrides: Partial<VideoOut> = {}): VideoOut {
	return {
		id: 'vid-1',
		channel_id: 'ch-1',
		title: 'Video One',
		description: null,
		thumbnail_url: null,
		published_at: '2026-01-01T00:00:00Z',
		duration_seconds: 120,
		yt_tags: [],
		is_short: false,
		is_favorited: false,
		is_watched: false,
		created_at: '2026-01-01T00:00:00Z',
		tag_ids: [],
		...overrides
	};
}

describe('SaveVideoModal', () => {
	beforeEach(() => {
		listMock.mockReset();
		getMock.mockReset();
		createMock.mockReset();
		addVideoMock.mockReset();
		removeVideoMock.mockReset();

		listMock.mockResolvedValue({
			items: [makePlaylist({ id: 'pl-a', name: 'A' }), makePlaylist({ id: 'pl-b', name: 'B' })],
			total: 2,
			limit: 200,
			offset: 0,
			has_more: false
		});
		getMock.mockImplementation((playlistId: string) =>
			Promise.resolve({
				id: playlistId,
				name: playlistId,
				description: null,
				is_system: false,
				source_type: 'manual',
				source_channel_id: null,
				source_is_active: true,
				current_position: null,
				total_videos: playlistId === 'pl-a' ? 1 : 0,
				created_at: '2026-01-01T00:00:00Z',
				video_ids: playlistId === 'pl-a' ? ['vid-1'] : []
			})
		);
		createMock.mockResolvedValue(makePlaylist({ id: 'pl-new', name: 'New playlist' }));
		addVideoMock.mockResolvedValue({});
		removeVideoMock.mockResolvedValue(undefined);
	});

	it('pre-checks existing memberships and saves only add/remove deltas', async () => {
		const onClose = vi.fn();
		render(SaveVideoModal, {
			video: makeVideo(),
			onClose
		});

		const checkboxA = (await screen.findByLabelText('A')) as HTMLInputElement;
		const checkboxB = (await screen.findByLabelText('B')) as HTMLInputElement;

		expect(checkboxA.checked).toBe(true);
		expect(checkboxB.checked).toBe(false);

		await fireEvent.click(checkboxA); // remove from A
		await fireEvent.click(checkboxB); // add to B
		await fireEvent.click(screen.getByText(/^Save$/));

		await waitFor(() => {
			expect(addVideoMock).toHaveBeenCalledWith('pl-b', { video_id: 'vid-1' });
			expect(removeVideoMock).toHaveBeenCalledWith('pl-a', 'vid-1');
			expect(addVideoMock).toHaveBeenCalledTimes(1);
			expect(removeVideoMock).toHaveBeenCalledTimes(1);
			expect(onClose).toHaveBeenCalled();
		});
	});

	it('does not call add/remove when membership is unchanged', async () => {
		const onClose = vi.fn();
		render(SaveVideoModal, {
			video: makeVideo(),
			onClose
		});

		await screen.findByLabelText('A');
		await fireEvent.click(screen.getByText(/^Save$/));

		await waitFor(() => {
			expect(addVideoMock).not.toHaveBeenCalled();
			expect(removeVideoMock).not.toHaveBeenCalled();
			expect(onClose).toHaveBeenCalled();
		});
	});
});
