<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { authApi } from '$lib/api/auth';
	import { authState } from '$lib/stores/authState.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let email = $state('');
	let password = $state('');
	let isSubmitting = $state(false);
	let errorMessage = $state<string | null>(null);

	const nextPath = $derived(page.url.searchParams.get('next') ?? '/inbox');
	const registered = $derived(page.url.searchParams.get('registered') === '1');

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		errorMessage = null;
		isSubmitting = true;

		try {
			const result = await authApi.login(email.trim(), password);
			if (!result.ok) {
				errorMessage = result.error ?? 'LOGIN_FAILED';
				return;
			}

			await authState.initialize();
			goto(resolve(nextPath as '/inbox'), { replaceState: true });
		} finally {
			isSubmitting = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-base-200 px-4">
	<div class="card w-full max-w-md border border-base-300 bg-base-100 shadow-sm">
		<div class="card-body">
			<h1 class="card-title text-2xl">Log in</h1>
			<p class="text-sm text-base-content/70">Access your ChooseYourTube account.</p>

			{#if registered}
				<div class="mt-2 alert alert-success">
					<span>Account created. You can log in now.</span>
				</div>
			{/if}

			{#if errorMessage}
				<div class="mt-2 alert alert-error">
					<span>{errorMessage}</span>
				</div>
			{/if}

			<form class="mt-4 space-y-4" onsubmit={handleSubmit}>
				<label class="form-control w-full">
					<span class="label-text">Email</span>
					<input
						type="email"
						class="input-bordered input w-full"
						bind:value={email}
						required
						autocomplete="email"
					/>
				</label>

				<label class="form-control w-full">
					<span class="label-text">Password</span>
					<input
						type="password"
						class="input-bordered input w-full"
						bind:value={password}
						required
						autocomplete="current-password"
					/>
				</label>

				<button class="btn w-full btn-primary" type="submit" disabled={isSubmitting}>
					{isSubmitting ? 'Logging in...' : 'Log in'}
				</button>
			</form>

			{#if data.metadata?.features.registration !== false}
				<p class="mt-3 text-sm text-base-content/70">
					Need an account?
					<a class="link link-primary" href={resolve('/register')}>Create one</a>
				</p>
			{/if}
		</div>
	</div>
</div>
