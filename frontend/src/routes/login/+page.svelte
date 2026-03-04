<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { authApi } from '$lib/api/auth';
	import { authState } from '$lib/stores/authState.svelte';

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
			goto(nextPath, { replaceState: true });
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
				<div class="alert alert-success mt-2">
					<span>Account created. You can log in now.</span>
				</div>
			{/if}

			{#if errorMessage}
				<div class="alert alert-error mt-2">
					<span>{errorMessage}</span>
				</div>
			{/if}

			<form class="mt-4 space-y-4" onsubmit={handleSubmit}>
				<label class="form-control w-full">
					<span class="label-text">Email</span>
					<input
						type="email"
						class="input input-bordered w-full"
						bind:value={email}
						required
						autocomplete="email"
					/>
				</label>

				<label class="form-control w-full">
					<span class="label-text">Password</span>
					<input
						type="password"
						class="input input-bordered w-full"
						bind:value={password}
						required
						autocomplete="current-password"
					/>
				</label>

				<button class="btn btn-primary w-full" type="submit" disabled={isSubmitting}>
					{isSubmitting ? 'Logging in...' : 'Log in'}
				</button>
			</form>

			<p class="mt-3 text-sm text-base-content/70">
				Need an account?
				<a class="link link-primary" href="/register">Create one</a>
			</p>
		</div>
	</div>
</div>
