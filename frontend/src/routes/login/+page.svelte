<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { enhance } from '$app/forms';
	import { page } from '$app/state';
	import { authApi } from '$lib/api/auth';
	import { authState } from '$lib/stores/authState.svelte';
	import type { PageData } from './$types';
	import { tick } from 'svelte';

	type LoginForm = {
		email?: string;
		message?: string;
		fieldErrors?: { email?: string; password?: string };
	};

	let { data, form }: { data: PageData; form?: LoginForm } = $props();

	let isSubmitting = $state(false);
	let errorMessage = $state<string | null>(null);
	let errorSummary = $state<HTMLDivElement>();

	const nextPath = $derived.by(() => {
		const candidate = page.url.searchParams.get('next');
		return candidate?.startsWith('/') && !candidate.startsWith('//') ? candidate : '/inbox';
	});
	const registered = $derived(page.url.searchParams.get('registered') === '1');
	const sessionExpired = $derived(page.url.searchParams.get('reason') === 'session_expired');

	async function handleDemoLogin() {
		errorMessage = null;
		isSubmitting = true;
		try {
			const result = await authApi.demoLogin();
			if (!result.ok) {
				errorMessage = result.error ?? 'The demo account is temporarily unavailable.';
				await tick();
				errorSummary?.focus();
				return;
			}
			await authState.initialize();
			goto(resolve(nextPath as '/inbox'), { replaceState: true });
		} catch {
			errorMessage = 'The demo account is temporarily unavailable. Please try again.';
			await tick();
			errorSummary?.focus();
		} finally {
			isSubmitting = false;
		}
	}
</script>

<svelte:head>
	<title>{data.metadata?.mode === 'demo' ? 'Try the Demo' : 'Log in'} - ChooseYourTube</title>
	<meta
		name="description"
		content="Sign in to ChooseYourTube, a distraction-free reader for your selected YouTube channels."
	/>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-base-200 px-4">
	<div class="card w-full max-w-md border border-base-300 bg-base-100 shadow-sm">
		<div class="card-body">
			<h1 class="card-title text-2xl">
				{data.metadata?.mode === 'demo' ? 'Explore ChooseYourTube' : 'Log in'}
			</h1>
			<p class="text-sm text-base-content/90">
				{data.metadata?.mode === 'demo'
					? 'Enter the shared demo without credentials. Changes reset daily.'
					: 'Access your ChooseYourTube account.'}
			</p>

			{#if registered}
				<div class="mt-2 alert alert-success" role="status">
					<span>Account created. You can log in now.</span>
				</div>
			{/if}
			{#if sessionExpired}
				<div class="mt-2 alert alert-warning" role="status">
					<span>Your session expired. Log in again to continue.</span>
				</div>
			{/if}

			{#if errorMessage || form?.message}
				<div class="mt-2 alert alert-error" role="alert" tabindex="-1" bind:this={errorSummary}>
					<span>{errorMessage ?? form?.message}</span>
				</div>
			{/if}

			{#if data.metadata?.features.demo_login}
				<button
					class="btn mt-4 w-full btn-primary"
					type="button"
					disabled={isSubmitting}
					onclick={handleDemoLogin}
				>
					{isSubmitting ? 'Entering demo…' : 'Try the demo'}
				</button>
			{:else}
				<form
					class="mt-4 space-y-4"
					method="POST"
					use:enhance={() => {
						isSubmitting = true;
						errorMessage = null;
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
					<input type="hidden" name="next" value={nextPath} />
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
							aria-describedby={form?.fieldErrors?.email ? 'login-email-error' : undefined}
						/>
					</label>
					{#if form?.fieldErrors?.email}
						<p id="login-email-error" class="text-sm text-error">{form.fieldErrors.email}</p>
					{/if}

					<label class="form-control w-full">
						<span class="label-text">Password</span>
						<input
							name="password"
							type="password"
							class="input-bordered input w-full"
							required
							autocomplete="current-password"
							aria-invalid={form?.fieldErrors?.password ? 'true' : undefined}
							aria-describedby={form?.fieldErrors?.password ? 'login-password-error' : undefined}
						/>
					</label>
					{#if form?.fieldErrors?.password}
						<p id="login-password-error" class="text-sm text-error">
							{form.fieldErrors.password}
						</p>
					{/if}

					<button class="btn w-full btn-primary" type="submit" disabled={isSubmitting}>
						{isSubmitting ? 'Logging in...' : 'Log in'}
					</button>
				</form>

				{#if data.metadata?.features.registration !== false}
					<p class="mt-3 text-sm text-base-content/90">
						Need an account?
						<a class="link link-primary" href={resolve('/register')}>Create one</a>
					</p>
				{/if}
			{/if}
		</div>
	</div>
</div>
