import type { ChannelOut, FolderOut } from '$lib/types/api';

/**
 * Discriminated union — type: 'none' means no modal is open.
 */
export type ModalState =
	| { type: 'none' }
	| { type: 'addChannel' }
	| { type: 'createFolder' }
	| { type: 'editChannel'; channel: ChannelOut }
	| { type: 'editFolder'; folder: FolderOut };

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
export function openCreateFolder() {
	modalState.current = { type: 'createFolder' };
}
export function openEditChannel(channel: ChannelOut) {
	modalState.current = { type: 'editChannel', channel };
}
export function openEditFolder(folder: FolderOut) {
	modalState.current = { type: 'editFolder', folder };
}
export function closeModal() {
	modalState.current = { type: 'none' };
}
