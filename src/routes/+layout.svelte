<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import TopBar from '$lib/components/layout/TopBar.svelte';
	import YouTubePlayerDock from '$lib/components/player/YouTubePlayerDock.svelte';
	import AddChannelModal from '$lib/components/modals/AddChannelModal.svelte';
	import CreateFolderModal from '$lib/components/modals/CreateFolderModal.svelte';
	import { playerState } from '$lib/stores/playerState.svelte';

	interface Props {
		children: any;
		data: {
			folders: any[];
			unfolderedChannels: any[];
		};
	}

	let { children, data }: Props = $props();

	let showAddChannelModal = $state(false);
	let showCreateFolderModal = $state(false);
	function openAddChannelModal() {
		console.log('🔍 LAYOUT: openAddChannelModal called');
		console.log('🔍 LAYOUT: showAddChannelModal BEFORE:', showAddChannelModal);
		showAddChannelModal = true;
		console.log('🔍 LAYOUT: showAddChannelModal AFTER:', showAddChannelModal);
	}
	function closeAddChannelModal() {
		showAddChannelModal = false;
	}
	function openCreateFolderModal() {
		console.log('🔍 LAYOUT: openCreateFolderModal called');
		console.log('🔍 LAYOUT: showCreateFolderModal BEFORE:', showCreateFolderModal);
		showCreateFolderModal = true;
		console.log('🔍 LAYOUT: showCreateFolderModal AFTER:', showCreateFolderModal);
	}
	function closeCreateFolderModal() {
		showCreateFolderModal = false;
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="app-shell flex h-screen overflow-hidden">
	<!-- Sidebar -->
	<Sidebar
		folders={data.folders}
		unfolderedChannels={data.unfolderedChannels}
		onOpenAddChannel={openAddChannelModal}
		onOpenCreateFolder={openCreateFolderModal}
	/>

	<!-- Main content area -->
	<div class="flex flex-1 flex-col overflow-hidden">
		<!-- Top bar -->
		<TopBar />

		<!-- Main content -->
		<main class="bg-base-200 flex-1 overflow-auto">
			{@render children()}
		</main>
	</div>

	<!-- YouTube Player Dock (shown when video is playing) -->
	{#if playerState.current.currentVideo}
		<YouTubePlayerDock />
	{/if}
</div>

<!-- Modals - rendered at root level to escape overflow constraints -->
{#if showAddChannelModal}
	{console.log('🔍 LAYOUT: Rendering AddChannelModal')}
	<AddChannelModal folders={data.folders} onClose={closeAddChannelModal} />
{/if}
{#if showCreateFolderModal}
	{console.log('🔍 LAYOUT: Rendering CreateFolderModal')}
	<CreateFolderModal folders={data.folders} onClose={closeCreateFolderModal} />
{/if}
