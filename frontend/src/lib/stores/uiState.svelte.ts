export type VideoDisplayMode = 'list' | 'grid' | 'compact';

const videoDisplayModes: VideoDisplayMode[] = ['list', 'grid', 'compact'];

export function isVideoDisplayMode(value: unknown): value is VideoDisplayMode {
	return videoDisplayModes.includes(value as VideoDisplayMode);
}

/**
 * UI state interface
 */
interface UIState {
	sidebarCollapsed: boolean;
	mobileSidebarOpen: boolean;
	sidebarWidth: number;
	pageSize: number;
	videoDisplayMode: VideoDisplayMode;
}

/**
 * Default UI state
 */
const defaultState: UIState = {
	sidebarCollapsed: false,
	mobileSidebarOpen: false,
	sidebarWidth: 280,
	pageSize: 24,
	videoDisplayMode: 'list'
};

/**
 * Load state from localStorage
 */
function loadState(): UIState {
	if (typeof window === 'undefined') return defaultState;

	try {
		const stored = localStorage.getItem('cyt:ui');
		const parsed = stored ? (JSON.parse(stored) as Partial<UIState>) : {};
		return {
			sidebarCollapsed: parsed.sidebarCollapsed ?? defaultState.sidebarCollapsed,
			mobileSidebarOpen: false,
			sidebarWidth: parsed.sidebarWidth ?? defaultState.sidebarWidth,
			pageSize: parsed.pageSize ?? defaultState.pageSize,
			videoDisplayMode: isVideoDisplayMode(parsed.videoDisplayMode)
				? parsed.videoDisplayMode
				: defaultState.videoDisplayMode
		};
	} catch {
		return defaultState;
	}
}

/**
 * Save state to localStorage
 */
function saveState(state: UIState) {
	if (typeof window === 'undefined') return;

	try {
		localStorage.setItem('cyt:ui', JSON.stringify(state));
	} catch (error) {
		console.error('Failed to save UI state:', error);
	}
}

/**
 * Create reactive UI state
 */
function createUIState() {
	let state = $state<UIState>(loadState());

	return {
		get current() {
			return state;
		},
		set current(value: UIState) {
			state = value;
			saveState(state);
		},
		update(fn: (state: UIState) => UIState) {
			state = fn(state);
			saveState(state);
		}
	};
}

export const uiState = createUIState();

/**
 * Toggle sidebar collapsed state
 */
export function toggleSidebar() {
	uiState.update((state) => ({
		...state,
		sidebarCollapsed: !state.sidebarCollapsed
	}));
}

export function openMobileSidebar() {
	uiState.update((state) => ({ ...state, mobileSidebarOpen: true }));
}

export function closeMobileSidebar() {
	const wasOpen = uiState.current.mobileSidebarOpen;
	uiState.update((state) => ({ ...state, mobileSidebarOpen: false }));
	if (wasOpen && typeof document !== 'undefined') {
		queueMicrotask(() => document.getElementById('mobile-nav-trigger')?.focus());
	}
}

/**
 * Set sidebar width
 */
export function setSidebarWidth(width: number) {
	uiState.update((state) => ({
		...state,
		sidebarWidth: Math.max(200, Math.min(400, width))
	}));
}

/**
 * Set page size for paginated views
 */
export function setPageSize(size: number) {
	const allowed = [12, 24, 48, 100];
	uiState.update((state) => ({
		...state,
		pageSize: allowed.includes(size) ? size : 24
	}));
}

/**
 * Set the global video-list display preference.
 */
export function setVideoDisplayMode(mode: VideoDisplayMode) {
	uiState.update((state) => ({
		...state,
		videoDisplayMode: mode
	}));
}
