<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import type { PageData } from './$types';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import ErrorState from '$lib/components/ui/ErrorState.svelte';
	import PaginationControls from '$lib/components/ui/PaginationControls.svelte';
	import { api } from '$lib/api';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let name = $state('');
	let description = $state('');
	let isSubmitting = $state(false);
	let submitError = $state<string | null>(null);

	async function handleCreatePlaylist(e: Event) {
		e.preventDefault();
		if (!name.trim()) return;

		isSubmitting = true;
		submitError = null;

		try {
			const playlist = await api.playlists.create({
				name: name.trim(),
				description: description.trim() || undefined
			});
			name = '';
			description = '';
			await goto(`/playlists/${playlist.id}`);
		} catch (err) {
			submitError = err instanceof Error ? err.message : 'Failed to create playlist';
		} finally {
			isSubmitting = false;
		}
	}

	async function refreshPlaylists() {
		await invalidateAll();
	}
</script>

<svelte:head>
	<title>Playlists - ChooseYourTube</title>
</svelte:head>

<div class="container mx-auto max-w-7xl p-6">
	<div class="mb-6 flex items-start justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold">Playlists</h1>
			<p class="text-sm text-base-content/60">{data.total} {data.total === 1 ? 'playlist' : 'playlists'}</p>
		</div>
		<button class="btn btn-sm btn-ghost" onclick={refreshPlaylists}>Refresh</button>
	</div>

	<div class="mb-6 rounded-box border border-base-300 bg-base-100 p-4">
		<h2 class="mb-3 text-lg font-semibold">Create Playlist</h2>
		<form onsubmit={handleCreatePlaylist} class="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
			<div>
				<label class="label" for="playlist-name">
					<span class="label-text">Name</span>
				</label>
				<input
					id="playlist-name"
					type="text"
					class="input-bordered input w-full"
					bind:value={name}
					disabled={isSubmitting}
					required
				/>
			</div>
			<div>
				<label class="label" for="playlist-description">
					<span class="label-text">Description (optional)</span>
				</label>
				<input
					id="playlist-description"
					type="text"
					class="input-bordered input w-full"
					bind:value={description}
					disabled={isSubmitting}
				/>
			</div>
			<button class="btn btn-primary" type="submit" disabled={isSubmitting || !name.trim()}>
				{#if isSubmitting}
					<span class="loading loading-sm loading-spinner"></span>
				{/if}
				Create
			</button>
		</form>
		{#if submitError}
			<p class="mt-2 text-sm text-error">{submitError}</p>
		{/if}
	</div>

	{#if data.error}
		<ErrorState message={data.error} />
	{:else if data.playlists.length === 0}
		<EmptyState
			icon="folder"
			title="No playlists yet"
			message="Create a playlist to save videos for later."
		/>
	{:else}
		<div class="space-y-3">
			{#each data.playlists as playlist (playlist.id)}
				<a
					href={`/playlists/${playlist.id}`}
					class="card border border-base-300 bg-base-100 transition-colors hover:border-primary"
				>
					<div class="card-body p-4">
						<div class="flex items-start gap-4">
							<div class="h-24 w-40 shrink-0 overflow-hidden rounded-box bg-base-200">
								{#if playlist.display_thumbnail_url}
									<img
										src={playlist.display_thumbnail_url}
										alt={playlist.name}
										class="h-full w-full object-cover"
									/>
								{:else}
									<div
										class="flex h-full w-full items-center justify-center text-base-content/40"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											fill="none"
											viewBox="0 0 24 24"
											stroke-width="1.5"
											stroke="currentColor"
											class="h-8 w-8"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												d="M9 9l10.5-3m0 0L21 16.5M19.5 6L9 9m0 0l-1.5 10.5M9 9L3 7.5m4.5 12L3 7.5m0 0L13.5 4.5"
											/>
										</svg>
									</div>
								{/if}
							</div>
							<div class="min-w-0">
								<h2 class="truncate font-semibold">{playlist.name}</h2>
								<p class="text-sm text-base-content/60">{playlist.total_videos} videos</p>
								{#if playlist.description}
									<p class="mt-1 line-clamp-2 text-sm text-base-content/70">{playlist.description}</p>
								{/if}
							</div>
						</div>
					</div>
				</a>
			{/each}
		</div>

		<PaginationControls
			total={data.total}
			currentPage={data.page}
			pageSize={data.pageSize}
			basePath="/playlists"
		/>
	{/if}
</div>
