<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { authApi } from '$lib/api/auth';

	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let isSubmitting = $state(false);
	let errorMessage = $state<string | null>(null);

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		errorMessage = null;

		if (password !== confirmPassword) {
			errorMessage = 'Passwords do not match';
			return;
		}

		isSubmitting = true;
		try {
			const result = await authApi.register(email.trim(), password);
			if (!result.ok) {
				errorMessage = result.error ?? 'REGISTER_FAILED';
				return;
			}
			goto(resolve('/login?registered=1' as '/login'), { replaceState: true });
		} finally {
			isSubmitting = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-base-200 px-4">
	<div class="card w-full max-w-md border border-base-300 bg-base-100 shadow-sm">
		<div class="card-body">
			<h1 class="card-title text-2xl">Create account</h1>
			<p class="text-sm text-base-content/70">Register a new ChooseYourTube user.</p>

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
						autocomplete="new-password"
					/>
				</label>

				<label class="form-control w-full">
					<span class="label-text">Confirm password</span>
					<input
						type="password"
						class="input-bordered input w-full"
						bind:value={confirmPassword}
						required
						autocomplete="new-password"
					/>
				</label>

				<button class="btn w-full btn-primary" type="submit" disabled={isSubmitting}>
					{isSubmitting ? 'Creating account...' : 'Create account'}
				</button>
			</form>

			<p class="mt-3 text-sm text-base-content/70">
				Already have an account?
				<a class="link link-primary" href={resolve('/login')}>Log in</a>
			</p>
		</div>
	</div>
</div>
