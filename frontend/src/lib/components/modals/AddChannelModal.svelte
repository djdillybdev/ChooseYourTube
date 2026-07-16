<script lang="ts">
	import { api } from '$lib/api';
	import type { CategoryOut } from '$lib/types/api';
	import { invalidate } from '$app/navigation';
	import { resolve } from '$app/paths';
	import DialogShell from '$lib/components/ui/DialogShell.svelte';
	import SyncStatus from '$lib/components/channel/SyncStatus.svelte';
	import type { ChannelCreateResult, SyncRunOut } from '$lib/types/api';
	import { APIError } from '$lib/types/api';
	import { pollSyncRun } from '$lib/utils/syncPolling';
	import { onDestroy } from 'svelte';

	interface Props {
		categories: CategoryOut[];
		onClose: () => void;
		onSuccess?: () => void;
	}

	let { categories, onClose, onSuccess }: Props = $props();

	let handle = $state('');
	let selectedCategoryIds = $state<string[]>([]);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);
	let fieldError = $state<string | null>(null);
	let result = $state<ChannelCreateResult | null>(null);
	let sync = $state<SyncRunOut | null>(null);
	let categoryError = $state<string | null>(null);
	let pollingError = $state<string | null>(null);
	let cancelled = false;

	onDestroy(() => {
		cancelled = true;
	});

	function inputError(err: unknown): string | null {
		if (!(err instanceof APIError)) return null;
		if (err.code === 'VALIDATION_ERROR') {
			return 'Use an @handle or a youtube.com URL containing an @handle.';
		}
		if (err.code === 'CHANNEL_ALREADY_FOLLOWED') return 'This channel is already in your library.';
		if (err.code === 'YOUTUBE_CHANNEL_NOT_FOUND') {
			return 'That channel could not be found or is not publicly available.';
		}
		return null;
	}

	async function poll(run: SyncRunOut) {
		if (run.status !== 'queued' && run.status !== 'running') return;
		try {
			await pollSyncRun(
				run.id,
				api.syncRuns.get.bind(api.syncRuns),
				(update) => (sync = update),
				() => cancelled
			);
		} catch {
			pollingError =
				'Live sync updates are unavailable. You can view the channel or check Sync Activity.';
		}
	}

	async function assignCategories(channelId: string) {
		if (selectedCategoryIds.length === 0) return true;
		try {
			await api.categories.setForChannel(channelId, { category_ids: selectedCategoryIds });
			categoryError = null;
			await invalidate('app:categories');
			return true;
		} catch {
			categoryError = 'The channel was followed, but its categories could not be assigned.';
			return false;
		}
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!handle.trim()) return;

		isSubmitting = true;
		error = null;
		fieldError = null;

		try {
			result = await api.channels.create({ handle: handle.trim() });
			sync = result.initial_sync;
			await invalidate('app:channels');
			await assignCategories(result.channel.id);
			onSuccess?.();
			void poll(result.initial_sync);
		} catch (err) {
			fieldError = inputError(err);
			error = fieldError
				? null
				: err instanceof Error
					? err.message
					: 'The channel could not be followed. Please try again.';
		} finally {
			isSubmitting = false;
		}
	}

	async function retrySync() {
		if (!sync) return;
		isSubmitting = true;
		pollingError = null;
		try {
			sync = await api.syncRuns.retry(sync.id);
			void poll(sync);
		} catch (err) {
			pollingError = err instanceof Error ? err.message : 'Synchronization could not be retried.';
		} finally {
			isSubmitting = false;
		}
	}

	async function retryCategories() {
		if (!result) return;
		isSubmitting = true;
		await assignCategories(result.channel.id);
		isSubmitting = false;
	}
</script>

<DialogShell
	id="add-channel-dialog"
	titleId="add-channel-title"
	descriptionId="add-channel-description"
	busy={isSubmitting}
	{onClose}
>
	<h2 id="add-channel-title" class="text-lg font-bold">
		{result ? 'Channel followed' : 'Add YouTube Channel'}
	</h2>
	<p id="add-channel-description" class="py-2 text-sm text-base-content/80">
		{result
			? `${result.channel.title} is now in your library.`
			: 'Enter a channel handle, such as @mkbhd, or a YouTube URL containing an @handle.'}
	</p>

	{#if result && sync}
		<div class="space-y-4" aria-live="polite">
			<SyncStatus {sync} />
			<p class="text-sm">
				{sync.status === 'failed'
					? 'Channel followed, but videos could not be synchronized.'
					: sync.status === 'partial'
						? 'The channel is ready, but some videos could not be synchronized.'
						: sync.status === 'succeeded'
							? 'The channel and its latest videos are ready.'
							: sync.status === 'running'
								? 'The channel is followed and its videos are synchronizing now.'
								: 'The channel is followed and video synchronization is queued.'}
			</p>
			{#if categoryError}
				<div class="alert alert-warning" role="alert">
					<span>{categoryError}</span>
					<button type="button" class="btn btn-sm" disabled={isSubmitting} onclick={retryCategories}
						>Retry categories</button
					>
				</div>
			{/if}
			{#if pollingError}<div class="alert alert-warning" role="alert">{pollingError}</div>{/if}
			<div class="modal-action flex-wrap">
				{#if sync.status === 'failed' && sync.retryable}
					<button class="btn" type="button" disabled={isSubmitting} onclick={retrySync}>
						{isSubmitting ? 'Retrying…' : 'Retry sync'}
					</button>
				{/if}
				<a
					class="btn btn-outline"
					href={resolve('/channels/[id]', { id: result.channel.id })}
					onclick={onClose}>View channel</a
				>
				<button type="button" class="btn btn-primary" onclick={onClose}>Done</button>
			</div>
		</div>
	{:else}
		<a class="link text-sm link-primary" href={resolve('/settings/imports')} onclick={onClose}>
			Import subscriptions from YouTube
		</a>

		<form onsubmit={handleSubmit} class="space-y-4">
			<!-- Channel handle input -->
			<div class="form-control">
				<label class="label" for="channel-handle">
					<span class="label-text">Channel Handle or URL</span>
				</label>
				<input
					id="channel-handle"
					data-dialog-initial-focus
					type="text"
					placeholder="@channelhandle"
					bind:value={handle}
					disabled={isSubmitting}
					class="input-bordered input w-full"
					required
					aria-invalid={fieldError ? 'true' : undefined}
					aria-describedby={fieldError ? 'channel-handle-error' : undefined}
				/>
			</div>
			{#if fieldError}<p id="channel-handle-error" class="text-sm text-error">{fieldError}</p>{/if}

			<fieldset>
				<legend class="label-text mb-2">Categories (optional)</legend>
				{#if categories.length === 0}
					<p class="text-sm text-base-content/60">You can categorize this channel later.</p>
				{:else}
					<div class="flex flex-wrap gap-2">
						{#each categories as category (category.id)}
							<label class="label cursor-pointer gap-2 rounded border border-base-300 px-2 py-1">
								<input
									type="checkbox"
									class="checkbox checkbox-xs"
									checked={selectedCategoryIds.includes(category.id)}
									onchange={(event) => {
										selectedCategoryIds = event.currentTarget.checked
											? [...new Set([...selectedCategoryIds, category.id])]
											: selectedCategoryIds.filter((id) => id !== category.id);
									}}
								/>
								<span>{category.name}</span>
							</label>
						{/each}
					</div>
				{/if}
			</fieldset>

			<!-- Error message -->
			{#if error}
				<div class="alert alert-error" role="alert">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6 shrink-0 stroke-current"
						fill="none"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<span>{error}</span>
				</div>
			{/if}

			<!-- Actions -->
			<div class="modal-action">
				<button type="button" class="btn btn-ghost" onclick={onClose} disabled={isSubmitting}>
					Cancel
				</button>
				<button type="submit" class="btn btn-primary" disabled={isSubmitting || !handle.trim()}>
					{#if isSubmitting}
						<span class="loading loading-sm loading-spinner"></span>
						Adding...
					{:else}
						Add Channel
					{/if}
				</button>
			</div>
		</form>
	{/if}
</DialogShell>
