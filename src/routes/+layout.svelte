<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import TopBar from '$lib/components/layout/TopBar.svelte';
	import YouTubePlayerDock from '$lib/components/player/YouTubePlayerDock.svelte';
	import { playerState } from '$lib/stores/playerState.svelte';

	interface Props {
		children: any;
		data: {
			folders: any[];
		};
	}

	let { children, data }: Props = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="app-shell flex h-screen overflow-hidden">
	<!-- Sidebar -->
	<Sidebar folders={data.folders} />

	<!-- Main content area -->
	<div class="flex flex-1 flex-col overflow-hidden">
		<!-- Top bar -->
		<TopBar />

		<!-- Main content -->
		<main class="flex-1 overflow-auto bg-base-200">
			{@render children()}
		</main>
	</div>

	<!-- YouTube Player Dock (shown when video is playing) -->
	{#if playerState.current.currentVideo}
		<YouTubePlayerDock />
	{/if}
</div>
