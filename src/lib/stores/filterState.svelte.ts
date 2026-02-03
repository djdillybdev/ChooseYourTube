/**
 * Filter state interface
 */
interface FilterState extends Record<string, unknown> {
	is_watched: boolean | undefined;
	is_favorited: boolean | undefined;
	is_short: boolean | undefined;
	channel_id: string | undefined;
	tag_id: string | undefined;
	folder_id: string | undefined;
	published_after: string | undefined;
	published_before: string | undefined;
}

/**
 * Default filter state
 * By default, show only unwatched videos in the inbox
 */
const defaultState: FilterState = {
	is_watched: false,
	is_favorited: undefined,
	is_short: undefined,
	channel_id: undefined,
	tag_id: undefined,
	folder_id: undefined,
	published_after: undefined,
	published_before: undefined
};

/**
 * Load state from localStorage
 */
function loadState(): FilterState {
	if (typeof window === 'undefined') return defaultState;

	try {
		const stored = localStorage.getItem('cyt:filters');
		return stored ? { ...defaultState, ...JSON.parse(stored) } : defaultState;
	} catch {
		return defaultState;
	}
}

/**
 * Save state to localStorage
 */
function saveState(state: FilterState) {
	if (typeof window === 'undefined') return;

	try {
		localStorage.setItem('cyt:filters', JSON.stringify(state));
	} catch (error) {
		console.error('Failed to save filter state:', error);
	}
}

/**
 * Create reactive filter state
 */
function createFilterState() {
	let state = $state<FilterState>(loadState());

	return {
		get current() {
			return state;
		},
		set current(value: FilterState) {
			state = value;
			saveState(state);
		},
		update(fn: (state: FilterState) => FilterState) {
			state = fn(state);
			saveState(state);
		}
	};
}

export const filterState = createFilterState();

/**
 * Set watched filter
 */
export function setWatchedFilter(value: boolean | undefined) {
	filterState.update((state) => ({
		...state,
		is_watched: value
	}));
}

/**
 * Set favorited filter
 */
export function setFavoritedFilter(value: boolean | undefined) {
	filterState.update((state) => ({
		...state,
		is_favorited: value
	}));
}

/**
 * Set shorts filter
 */
export function setShortsFilter(value: boolean | undefined) {
	filterState.update((state) => ({
		...state,
		is_short: value
	}));
}

/**
 * Set channel filter
 */
export function setChannelFilter(channelId: string | undefined) {
	filterState.update((state) => ({
		...state,
		channel_id: channelId
	}));
}

/**
 * Set tag filter
 */
export function setTagFilter(tagId: string | undefined) {
	filterState.update((state) => ({
		...state,
		tag_id: tagId
	}));
}

/**
 * Set folder filter
 */
export function setFolderFilter(folderId: string | undefined) {
	filterState.update((state) => ({
		...state,
		folder_id: folderId
	}));
}

/**
 * Set date range filter
 */
export function setDateRangeFilter(after?: string, before?: string) {
	filterState.update((state) => ({
		...state,
		published_after: after,
		published_before: before
	}));
}

/**
 * Clear all filters (reset to default)
 */
export function clearAllFilters() {
	filterState.current = defaultState;
}

/**
 * Clear a specific filter
 */
export function clearFilter(key: keyof FilterState) {
	filterState.update((state) => ({
		...state,
		[key]: undefined
	}));
}

/**
 * Check if any filters are active
 */
export function hasActiveFilters(state: FilterState): boolean {
	return Object.values(state).some((value) => value !== undefined);
}
