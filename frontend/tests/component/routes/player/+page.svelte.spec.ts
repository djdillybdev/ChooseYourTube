import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import PlayerPage from '../../../../src/routes/player/+page.svelte';

const { gotoMock, initializeQueueMock, openSaveVideoMock, playerStateMock } = vi.hoisted(() => {
	const currentVideo = {
		id: 'video-1',
		title: 'Theater Mode Test Video',
		description: 'A sample description',
		channel_id: 'channel-1'
	};

	return {
		gotoMock: vi.fn(),
		initializeQueueMock: vi.fn().mockResolvedValue(undefined),
		openSaveVideoMock: vi.fn(),
		playerStateMock: {
			current: {
				currentVideo,
				queue: [currentVideo],
				queueIndex: 0,
				isQueueReady: true,
				isQueueSyncing: false
			}
		},
		currentVideo
	};
});

vi.mock('$app/navigation', () => ({
	goto: gotoMock
}));

vi.mock('$lib/stores/playerState.svelte', () => ({
	playerState: playerStateMock,
	initializeQueue: initializeQueueMock
}));

vi.mock('$lib/stores/modalState.svelte', () => ({
	openSaveVideo: openSaveVideoMock
}));

vi.mock('$lib/components/player/YouTubePlayer.svelte', async () => {
	const module = await import('../../stubs/YouTubePlayerStub.svelte');
	return { default: module.default };
});

vi.mock('$lib/components/player/QueueList.svelte', async () => {
	const module = await import('../../stubs/QueueListStub.svelte');
	return { default: module.default };
});

describe('player route layout', () => {
	const pageData = {
		isPublicAuthRoute: false,
		currentUser: null,
		folders: [],
		categories: [],
		uncategorizedChannels: [],
		channels: [],
		tags: [],
		watchLater: null,
		runtime: {
			name: 'ChooseYourTube',
			version: '0.1.0',
			mode: 'full' as const,
			features: {
				registration: true,
				background_jobs: true,
				youtube_oauth: false,
				demo_login: false,
				subscription_imports: true
			}
		}
	};

	beforeEach(() => {
		vi.stubGlobal(
			'ResizeObserver',
			class ResizeObserver {
				constructor(private callback: ResizeObserverCallback) {}

				observe() {
					this.callback([], this as unknown as ResizeObserver);
				}

				unobserve() {}

				disconnect() {}
			}
		);

		vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function (
			this: HTMLElement
		) {
			if (this.classList.contains('player-stage')) {
				return {
					x: 0,
					y: 0,
					width: 1600,
					height: 600,
					top: 0,
					left: 0,
					right: 1600,
					bottom: 600,
					toJSON: () => ({})
				} as DOMRect;
			}

			return {
				x: 0,
				y: 0,
				width: 0,
				height: 0,
				top: 0,
				left: 0,
				right: 0,
				bottom: 0,
				toJSON: () => ({})
			} as DOMRect;
		});

		Object.defineProperty(window, 'innerWidth', {
			value: 1440,
			writable: true,
			configurable: true
		});
	});

	afterEach(() => {
		vi.unstubAllGlobals();
	});

	it('fits player frame to available area with explicit dimensions', async () => {
		const { container } = render(PlayerPage, {
			data: pageData
		});

		const layout = container.querySelector('.player-layout');
		expect(layout).toBeInTheDocument();

		const frame = container.querySelector('.player-frame') as HTMLElement;
		expect(frame).toBeInTheDocument();
		expect(frame).not.toHaveClass('max-w-4xl');

		await waitFor(() => {
			expect(frame.style.width).toBe('982px');
			expect(frame.style.height).toBe('552px');
		});

		expect(screen.getByTestId('youtube-player-stub')).toBeInTheDocument();
	});

	it('keeps fitted frame dimensions when queue panel is toggled on', async () => {
		const { container } = render(PlayerPage, {
			data: pageData
		});

		const frame = container.querySelector('.player-frame') as HTMLElement;

		await waitFor(() => {
			expect(frame.style.width).toBe('982px');
			expect(frame.style.height).toBe('552px');
		});

		await fireEvent.click(screen.getByRole('button', { name: /queue/i }));

		expect(screen.getByLabelText('Queue panel')).toBeInTheDocument();
		expect(screen.getByTestId('queue-list-stub')).toBeInTheDocument();
		expect(frame.style.width).toBe('982px');
		expect(frame.style.height).toBe('552px');
	});
});
