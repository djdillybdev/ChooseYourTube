<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';

	const safeMessage = $derived(
		page.status === 404
			? 'The requested page was not found.'
			: page.status === 401
				? 'Your session has ended. Log in to continue.'
				: page.error?.message || 'ChooseYourTube could not load this page.'
	);
</script>

<svelte:head>
	<title>Something went wrong - ChooseYourTube</title>
	<meta name="description" content="ChooseYourTube could not load this page." />
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-base-200 p-6">
	<div class="max-w-lg rounded-box border border-base-300 bg-base-100 p-6 text-center">
		<h1 class="text-2xl font-bold">This page could not be loaded</h1>
		<p class="mt-2 text-base-content/80">{safeMessage}</p>
		<div class="mt-5 flex flex-wrap justify-center gap-2">
			{#if page.status === 401}
				<a class="btn btn-primary" href={resolve('/login')}>Log in</a>
			{:else if page.status !== 404}
				<a class="btn btn-primary" href={resolve((page.url.pathname + page.url.search) as '/inbox')}
					>Try again</a
				>
			{/if}
			<a class="btn btn-outline" href={resolve('/inbox')}>Return to Inbox</a>
		</div>
	</div>
</div>
