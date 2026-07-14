/**
 * View mode options
 */
export type ViewMode = 'feed' | 'tv';

/**
 * Feed layout density options
 */
export type FeedLayout = 'compact' | 'comfortable' | 'list';

/**
 * UI state interface
 */
interface UIState {
	sidebarCollapsed: boolean;
	mobileSidebarOpen: boolean;
	sidebarWidth: number;
	viewMode: ViewMode;
	feedLayout: FeedLayout;
	tvGridColumns: number;
	pageSize: number;
}

/**
 * Default UI state
 */
const defaultState: UIState = {
	sidebarCollapsed: false,
	mobileSidebarOpen: false,
	sidebarWidth: 280,
	viewMode: 'feed',
	feedLayout: 'comfortable',
	tvGridColumns: 4,
	pageSize: 24
};

/**
 * Load state from localStorage
 */
function loadState(): UIState {
	if (typeof window === 'undefined') return defaultState;

	try {
		const stored = localStorage.getItem('cyt:ui');
		return stored ? { ...defaultState, ...JSON.parse(stored) } : defaultState;
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
 * Set view mode
 */
export function setViewMode(mode: ViewMode) {
	uiState.update((state) => ({
		...state,
		viewMode: mode
	}));
}

/**
 * Set feed layout density
 */
export function setFeedLayout(layout: FeedLayout) {
	uiState.update((state) => ({
		...state,
		feedLayout: layout
	}));
}

/**
 * Set TV grid column count
 */
export function setTVGridColumns(columns: number) {
	uiState.update((state) => ({
		...state,
		tvGridColumns: Math.max(2, Math.min(6, columns))
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
