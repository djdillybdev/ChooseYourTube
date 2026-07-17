import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import QueuePage from '../../../../src/routes/queue/+page.svelte';

const { gotoMock, initializeQueueMock, playerStateMock } = vi.hoisted(() => ({
	gotoMock: vi.fn(),
	initializeQueueMock: vi.fn().mockResolvedValue(undefined),
	playerStateMock: {
		current: {
			currentVideo: null,
			queue: [{ id: 'video-1' }],
			queueMode: 'system',
			isQueueReady: true,
			isQueueSyncing: false
		}
	}
}));

vi.mock('$app/navigation', () => ({
	goto: gotoMock
}));

vi.mock('$lib/stores/playerState.svelte', () => ({
	playerState: playerStateMock,
	initializeQueue: initializeQueueMock
}));

vi.mock('$lib/components/player/QueueList.svelte', async () => {
	const module = await import('../../stubs/QueueListStub.svelte');
	return { default: module.default };
});

describe('queue page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		initializeQueueMock.mockResolvedValue(undefined);
	});

	it('initializes the system queue and opens playback with a queue return URL', async () => {
		render(QueuePage, { data: { channels: [] } as never });

		await waitFor(() => expect(initializeQueueMock).toHaveBeenCalledWith(false));
		expect(screen.getByRole('heading', { name: 'Queue' })).toBeInTheDocument();
		expect(screen.getByTestId('queue-list-stub')).toHaveAttribute('data-variant', 'page');

		await fireEvent.click(screen.getByRole('button', { name: 'Play queued video' }));

		expect(gotoMock).toHaveBeenCalledWith('/player?return=%2Fqueue');
	});
});
