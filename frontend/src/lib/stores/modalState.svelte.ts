import type { CategoryOut, ChannelOut, VideoOut } from '$lib/types/api';

/**
 * Discriminated union — type: 'none' means no modal is open.
 */
export type ModalState =
	| { type: 'none' }
	| { type: 'addChannel' }
	| { type: 'createCategory' }
	| { type: 'editChannel'; channel: ChannelOut }
	| { type: 'editCategory'; category: CategoryOut }
	| { type: 'saveVideo'; video: VideoOut };

function createModalState() {
	let state = $state<ModalState>({ type: 'none' });

	return {
		get current() {
			return state;
		},
		set current(value: ModalState) {
			state = value;
		}
	};
}

export const modalState = createModalState();

/* ── Convenience openers ── import these anywhere ── */
export function openAddChannel() {
	modalState.current = { type: 'addChannel' };
}
export function openCreateCategory() {
	modalState.current = { type: 'createCategory' };
}
export function openEditChannel(channel: ChannelOut) {
	modalState.current = { type: 'editChannel', channel };
}
export function openEditCategory(category: CategoryOut) {
	modalState.current = { type: 'editCategory', category };
}
export function openSaveVideo(video: VideoOut) {
	modalState.current = { type: 'saveVideo', video };
}
export function closeModal() {
	modalState.current = { type: 'none' };
}
