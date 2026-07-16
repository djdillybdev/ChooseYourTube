<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { authApi } from '$lib/api/auth';
	import { page } from '$app/state';
	import DialogShell from '$lib/components/ui/DialogShell.svelte';

	let password = $state('');
	let confirming = $state(false);
	let busy = $state(false);
	let error = $state<string | null>(null);
	const demoMode = $derived(page.data.runtime?.mode === 'demo');

	function cancelDeletion(event?: Event) {
		event?.preventDefault();
		if (busy) return;
		confirming = false;
		password = '';
		error = null;
	}

	async function deleteAccount() {
		busy = true;
		error = null;
		try {
			const result = await authApi.deleteAccount(password);
			if (!result.ok) {
				error = result.error ?? 'Account deletion failed.';
				return;
			}
			await goto(resolve('/login'), { replaceState: true });
		} catch {
			error = 'Account deletion could not be completed. Please try again.';
		} finally {
			busy = false;
		}
	}
</script>

<svelte:head>
	<title>Account - Settings - ChooseYourTube</title>
	<meta name="description" content="Review ChooseYourTube account data and deletion options." />
</svelte:head>

<div class="container mx-auto max-w-6xl p-6 pt-5">
	<section class="rounded-box border border-base-300 bg-base-100 p-5">
		<h2 class="text-xl font-semibold">Your data</h2>
		<p class="mt-2 max-w-3xl text-sm text-base-content/70">
			ChooseYourTube stores your account, followed channels, cached video metadata, organization,
			playlists, viewing state, imports, and synchronization history. A bulk account export is not
			available in v1.0.
		</p>
		{#if demoMode}
			<div class="mt-5 alert alert-info">Account changes are disabled in the shared demo.</div>
		{:else}
			<div class="mt-6 border-t border-error/30 pt-5">
				<h3 class="font-semibold text-error">Delete account</h3>
				<p class="mt-1 text-sm text-base-content/70">
					Permanently deletes the account and all owned application data. This cannot be undone.
				</p>
				<button class="btn mt-4 btn-outline btn-error" onclick={() => (confirming = true)}>
					Delete my account
				</button>
				{#if confirming}
					<DialogShell
						id="delete-account-dialog"
						titleId="delete-account-title"
						descriptionId="delete-account-description"
						{busy}
						onClose={cancelDeletion}
						boxClass="max-w-md"
					>
						<h3 id="delete-account-title" class="text-lg font-bold">Permanently delete account?</h3>
						<p id="delete-account-description" class="mt-2 text-sm text-base-content/80">
							Enter your password to confirm. This permanently deletes all owned data.
						</p>
						<form
							onsubmit={(event) => {
								event.preventDefault();
								void deleteAccount();
							}}
						>
							<label for="delete-password" class="label">Current password</label>
							<input
								id="delete-password"
								type="password"
								autocomplete="current-password"
								class="input-bordered input w-full"
								bind:value={password}
								required
							/>
							{#if error}<p class="mt-2 text-sm text-error" role="alert">{error}</p>{/if}
							<div class="mt-4 flex gap-2">
								<button
									data-dialog-initial-focus
									type="button"
									class="btn btn-ghost"
									disabled={busy}
									onclick={cancelDeletion}
								>
									Cancel
								</button>
								<button type="submit" class="btn btn-error" disabled={busy || !password}>
									{busy ? 'Deleting…' : 'Permanently delete'}
								</button>
							</div>
						</form>
					</DialogShell>
				{/if}
			</div>
		{/if}
	</section>
</div>
