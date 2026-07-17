import { fireEvent, render, screen } from '@testing-library/svelte';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import QueueList from '../../../../../src/lib/components/player/QueueList.svelte';

const { clearQueueMock, jumpToQueueItemMock, playerStateMock } = vi.hoisted(() => ({
	clearQueueMock: vi.fn(),
	jumpToQueueItemMock: vi.fn(),
	playerStateMock: {
		current: {
			currentVideo: null as { id: string } | null,
			queue: [] as Array<{
				id: string;
				title: string;
				channel_id: string;
				thumbnail_url: string | null;
				duration_seconds: number | null;
			}>,
			queueIndex: 0,
			queueMode: 'system',
			queueMutable: true,
			isQueueSyncing: false,
			queueError: null as string | null
		}
	}
}));

vi.mock('$lib/stores/playerState.svelte', () => ({
	playerState: playerStateMock,
	jumpToQueueItem: jumpToQueueItemMock,
	removeFromQueue: vi.fn(),
	clearQueue: clearQueueMock,
	moveQueueItem: vi.fn()
}));

function video(id: string, title: string) {
	return {
		id,
		title,
		channel_id: 'channel-1',
		thumbnail_url: null,
		duration_seconds: 60
	};
}

describe('QueueList', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		playerStateMock.current = {
			...playerStateMock.current,
			currentVideo: null,
			queue: [video('one', 'First video'), video('two', 'Second video')]
		};
	});

	it('does not mark the first item active when nothing is playing', () => {
		render(QueueList);

		expect(screen.getByRole('button', { name: 'Play First video' })).not.toHaveAttribute(
			'aria-current'
		);
	});

	it('opens the player only after queue selection succeeds', async () => {
		const onPlaybackStarted = vi.fn();
		jumpToQueueItemMock.mockResolvedValue(true);
		render(QueueList, { onPlaybackStarted });

		await fireEvent.click(screen.getByRole('button', { name: 'Play Second video' }));

		expect(jumpToQueueItemMock).toHaveBeenCalledWith(1);
		expect(onPlaybackStarted).toHaveBeenCalledOnce();
	});

	it('hides clear when the current video is the only queue item', () => {
		const current = video('one', 'First video');
		playerStateMock.current = {
			...playerStateMock.current,
			currentVideo: current,
			queue: [current]
		};

		render(QueueList);

		expect(screen.queryByRole('button', { name: 'Clear queue' })).not.toBeInTheDocument();
	});
});
