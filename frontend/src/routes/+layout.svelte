<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import TopBar from '$lib/components/layout/TopBar.svelte';
	import type { ChannelOut, PlaylistDetailOut, TagOut, UserRead } from '$lib/types/api';
	import { modalState, closeModal } from '$lib/stores/modalState.svelte';
	import AddChannelModal from '$lib/components/modals/AddChannelModal.svelte';
	import CreateCategoryModal from '$lib/components/modals/CreateCategoryModal.svelte';
	import EditChannelModal from '$lib/components/modals/EditChannelModal.svelte';
	import EditCategoryModal from '$lib/components/modals/EditCategoryModal.svelte';
	import SaveVideoModal from '$lib/components/modals/SaveVideoModal.svelte';
	import type { Snippet } from 'svelte';
	import type { CategoryOut } from '$lib/types/api';
	import type { RuntimeMetadata } from '$lib/types/runtime';
	import { provideWatchLater } from '$lib/stores/watchLater.svelte';
	import DemoBanner from '$lib/components/layout/DemoBanner.svelte';
	import { uiState } from '$lib/stores/uiState.svelte';
	import { navigating } from '$app/state';
	import StatusHost from '$lib/components/ui/StatusHost.svelte';

	interface Props {
		children: Snippet;
		data: {
			isPublicAuthRoute?: boolean;
			currentUser: UserRead | null;
			categories: CategoryOut[];
			uncategorizedChannels: ChannelOut[];
			channels: ChannelOut[];
			tags: TagOut[];
			watchLater: PlaylistDetailOut | null;
			runtime: RuntimeMetadata;
		};
	}

	let { children, data }: Props = $props();
	const watchLaterState = provideWatchLater(null);
	const isNavigating = $derived(navigating.to !== null);
	$effect(() => watchLaterState.sync(data.watchLater));
</script>

<svelte:head>
	<title>ChooseYourTube</title>
	<link rel="icon" href={favicon} />
	<meta
		name="description"
		content="ChooseYourTube is a distraction-free feed reader for selected YouTube channels."
	/>
</svelte:head>

{#if data.isPublicAuthRoute}
	{@render children()}
{:else}
	<a class="skip-link" href="#main-content">Skip to content</a>
	<div class="sr-only" aria-live="polite" aria-atomic="true">
		{isNavigating ? 'Loading page' : ''}
	</div>
	<div class="app-shell flex h-screen overflow-hidden">
		<Sidebar
			categories={data.categories}
			uncategorizedChannels={data.uncategorizedChannels}
			channels={data.channels}
			backgroundJobsEnabled={data.runtime.features.background_jobs}
			demoMode={data.runtime.mode === 'demo'}
		/>

		<div
			class="flex min-w-0 flex-1 flex-col overflow-hidden"
			inert={uiState.current.mobileSidebarOpen ? true : undefined}
		>
			{#if isNavigating}
				<div
					class="h-1 w-full overflow-hidden bg-base-200"
					role="progressbar"
					aria-label="Loading page"
				>
					<div class="route-progress h-full w-1/3 bg-primary"></div>
				</div>
			{/if}
			<TopBar channels={data.channels} tags={data.tags} currentUser={data.currentUser} />
			{#if data.runtime.mode === 'demo'}<DemoBanner />{/if}
			<main id="main-content" tabindex="-1" class="flex-1 overflow-auto bg-base-200">
				{@render children()}
			</main>
		</div>
	</div>

	<!-- Modals - rendered outside app-shell to escape overflow:hidden -->
	{#if modalState.current.type === 'addChannel'}
		<AddChannelModal categories={data.categories} onClose={closeModal} />
	{/if}
	{#if modalState.current.type === 'createCategory'}
		<CreateCategoryModal onClose={closeModal} />
	{/if}
	{#if modalState.current.type === 'editChannel'}
		<EditChannelModal
			channel={modalState.current.channel}
			categories={data.categories}
			tags={data.tags}
			onClose={closeModal}
			demoMode={data.runtime.mode === 'demo'}
		/>
	{/if}
	{#if modalState.current.type === 'editCategory'}
		<EditCategoryModal
			category={modalState.current.category}
			channels={data.channels}
			onClose={closeModal}
		/>
	{/if}
	{#if modalState.current.type === 'saveVideo'}
		<SaveVideoModal video={modalState.current.video} tags={data.tags} onClose={closeModal} />
	{/if}
	<StatusHost />
{/if}
