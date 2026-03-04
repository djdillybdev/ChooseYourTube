<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import TopBar from '$lib/components/layout/TopBar.svelte';
	import type { ChannelOut, TagOut, UserRead } from '$lib/types/api';
	import { modalState, closeModal } from '$lib/stores/modalState.svelte';
	import AddChannelModal from '$lib/components/modals/AddChannelModal.svelte';
	import CreateFolderModal from '$lib/components/modals/CreateFolderModal.svelte';
	import EditChannelModal from '$lib/components/modals/EditChannelModal.svelte';
	import EditFolderModal from '$lib/components/modals/EditFolderModal.svelte';
	import SaveVideoModal from '$lib/components/modals/SaveVideoModal.svelte';

	interface Props {
		children: any;
		data: {
			isPublicAuthRoute?: boolean;
			currentUser: UserRead | null;
			folders: any[];
			unfolderedChannels: any[];
			channels: ChannelOut[];
			tags: TagOut[];
		};
	}

	let { children, data }: Props = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if data.isPublicAuthRoute}
	{@render children()}
{:else}
	<div class="app-shell flex h-screen overflow-hidden">
		<Sidebar
			folders={data.folders}
			unfolderedChannels={data.unfolderedChannels}
			channels={data.channels}
		/>

		<div class="flex flex-1 flex-col overflow-hidden">
			<TopBar channels={data.channels} tags={data.tags} currentUser={data.currentUser} />
			<main class="flex-1 overflow-auto bg-base-200">
				{@render children()}
			</main>
		</div>
	</div>

	<!-- Modals - rendered outside app-shell to escape overflow:hidden -->
	{#if modalState.current.type === 'addChannel'}
		<AddChannelModal folders={data.folders} onClose={closeModal} />
	{/if}
	{#if modalState.current.type === 'createFolder'}
		<CreateFolderModal folders={data.folders} onClose={closeModal} />
	{/if}
	{#if modalState.current.type === 'editChannel'}
		<EditChannelModal
			channel={modalState.current.channel}
			folders={data.folders}
			onClose={closeModal}
		/>
	{/if}
	{#if modalState.current.type === 'editFolder'}
		<EditFolderModal folder={modalState.current.folder} folders={data.folders} onClose={closeModal} />
	{/if}
	{#if modalState.current.type === 'saveVideo'}
		<SaveVideoModal video={modalState.current.video} onClose={closeModal} />
	{/if}
{/if}
