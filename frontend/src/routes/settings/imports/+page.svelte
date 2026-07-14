<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { api } from '$lib/api';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();
	let uploading = $state(false);
	let authorizing = $state(false);
	let error = $state<string | null>(null);

	async function upload(event: Event) {
		const input = event.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		uploading = true;
		error = null;
		try {
			const preview = await api.imports.uploadCSV(file);
			await goto(resolve(`/settings/imports/${preview.import.id}`));
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'The CSV could not be imported.';
		} finally {
			uploading = false;
			input.value = '';
		}
	}

	async function connectGoogle() {
		authorizing = true;
		error = null;
		try {
			const result = await api.imports.startOAuth();
			window.location.assign(result.authorization_url);
		} catch (cause) {
			error = cause instanceof Error ? cause.message : 'Google authorization could not start.';
			authorizing = false;
		}
	}
</script>

<svelte:head><title>Import Subscriptions - Settings - ChooseYourTube</title></svelte:head>

<div class="container mx-auto max-w-6xl p-6">
	<div class="mb-6">
		<h2 class="text-2xl font-bold">Import YouTube subscriptions</h2>
		<p class="text-base-content/60">Add channels without removing anything you already follow.</p>
	</div>

	{#if data.oauthError}
		<div class="mb-5 alert alert-error" role="alert">
			Google authorization expired, was cancelled, or could not be completed. Try again.
		</div>
	{/if}
	{#if error}<div class="mb-5 alert alert-error" role="alert">{error}</div>{/if}
	<div class="sr-only" aria-live="polite">
		{uploading ? 'Uploading subscription file' : authorizing ? 'Opening Google authorization' : ''}
	</div>

	{#if !data.runtime.features.subscription_imports}
		<div class="mb-6 alert alert-info">
			Subscription imports are disabled in the shared demo. The sample below shows the complete
			review experience available in the self-hosted app.
		</div>
		<div class="rounded-box bg-base-100 p-6 shadow-sm">
			<div class="mb-4 flex items-center justify-between">
				<h3 class="font-semibold">Sample completed import</h3>
				<span class="badge badge-success">succeeded</span>
			</div>
			<div class="stats w-full stats-vertical sm:stats-horizontal">
				<div class="stat">
					<div class="stat-title">Discovered</div>
					<div class="stat-value">24</div>
				</div>
				<div class="stat">
					<div class="stat-title">Imported</div>
					<div class="stat-value">18</div>
				</div>
				<div class="stat">
					<div class="stat-title">Already followed</div>
					<div class="stat-value">6</div>
				</div>
			</div>
		</div>
	{:else}
		<div class="grid gap-5 md:grid-cols-2">
			<section class="card bg-base-100 shadow-sm">
				<div class="card-body">
					<h3 class="card-title">Google Takeout CSV</h3>
					<p>Upload the subscriptions CSV from your Google Takeout YouTube export.</p>
					<p class="text-sm text-base-content/60">Maximum 2 MB and 5,000 rows.</p>
					<label class="btn mt-auto btn-primary" class:btn-disabled={uploading}>
						{uploading ? 'Uploading…' : 'Choose CSV'}
						<input
							type="file"
							accept=".csv,text/csv"
							class="sr-only"
							disabled={uploading}
							onchange={upload}
						/>
					</label>
				</div>
			</section>
			<section class="card bg-base-100 shadow-sm">
				<div class="card-body">
					<h3 class="card-title">Google account</h3>
					<p>Authorize one-time read-only access to collect your YouTube subscriptions.</p>
					<p class="text-sm text-base-content/60">Credentials are discarded after discovery.</p>
					<button
						class="btn mt-auto btn-primary"
						disabled={!data.runtime.features.youtube_oauth || authorizing}
						onclick={connectGoogle}
					>
						{authorizing ? 'Connecting…' : 'Continue with Google'}
					</button>
					{#if !data.runtime.features.youtube_oauth}
						<p class="text-sm text-warning">Google OAuth is not configured on this installation.</p>
					{/if}
				</div>
			</section>
		</div>
	{/if}
</div>
