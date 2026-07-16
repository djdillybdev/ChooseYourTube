<script lang="ts">
	import { enhance } from '$app/forms';
	import { resolve } from '$app/paths';
	import { tick } from 'svelte';

	type RegisterForm = {
		email?: string;
		message?: string;
		fieldErrors?: { email?: string; password?: string; confirmPassword?: string };
	};

	let { form }: { form?: RegisterForm } = $props();
	let isSubmitting = $state(false);
	let errorSummary = $state<HTMLDivElement>();
</script>

<svelte:head>
	<title>Create Account - ChooseYourTube</title>
	<meta name="description" content="Create a self-hosted ChooseYourTube account." />
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-base-200 px-4">
	<div class="card w-full max-w-md border border-base-300 bg-base-100 shadow-sm">
		<div class="card-body">
			<h1 class="card-title text-2xl">Create account</h1>
			<p class="text-sm text-base-content/70">Register a new ChooseYourTube user.</p>

			{#if form?.message}
				<div class="mt-2 alert alert-error" role="alert" tabindex="-1" bind:this={errorSummary}>
					<span>{form.message}</span>
				</div>
			{/if}

			<form
				class="mt-4 space-y-4"
				method="POST"
				use:enhance={() => {
					isSubmitting = true;
					return async ({ update, result }) => {
						await update();
						isSubmitting = false;
						if (result.type === 'failure') {
							await tick();
							errorSummary?.focus();
						}
					};
				}}
			>
				<label class="form-control w-full">
					<span class="label-text">Email</span>
					<input
						name="email"
						type="email"
						class="input-bordered input w-full"
						value={form?.email ?? ''}
						required
						autocomplete="email"
						aria-invalid={form?.fieldErrors?.email ? 'true' : undefined}
						aria-describedby={form?.fieldErrors?.email ? 'register-email-error' : undefined}
					/>
				</label>
				{#if form?.fieldErrors?.email}
					<p id="register-email-error" class="text-sm text-error">{form.fieldErrors.email}</p>
				{/if}

				<label class="form-control w-full">
					<span class="label-text">Password</span>
					<input
						name="password"
						type="password"
						class="input-bordered input w-full"
						required
						autocomplete="new-password"
						aria-invalid={form?.fieldErrors?.password ? 'true' : undefined}
						aria-describedby={form?.fieldErrors?.password ? 'register-password-error' : undefined}
					/>
				</label>
				{#if form?.fieldErrors?.password}
					<p id="register-password-error" class="text-sm text-error">
						{form.fieldErrors.password}
					</p>
				{/if}

				<label class="form-control w-full">
					<span class="label-text">Confirm password</span>
					<input
						name="confirmPassword"
						type="password"
						class="input-bordered input w-full"
						required
						autocomplete="new-password"
						aria-invalid={form?.fieldErrors?.confirmPassword ? 'true' : undefined}
						aria-describedby={form?.fieldErrors?.confirmPassword
							? 'register-confirm-error'
							: undefined}
					/>
				</label>
				{#if form?.fieldErrors?.confirmPassword}
					<p id="register-confirm-error" class="text-sm text-error">
						{form.fieldErrors.confirmPassword}
					</p>
				{/if}

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
