<script lang="ts">
	import { page } from '$app/state';
</script>

<svelte:head>
	<title>Something went wrong - ChooseYourTube</title>
	<meta name="description" content="ChooseYourTube could not load this page." />
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-base-200 p-6">
	<div class="max-w-lg rounded-box border border-base-300 bg-base-100 p-6 text-center">
		<h1 class="text-2xl font-bold">This page could not be loaded</h1>
		<p class="mt-2 text-base-content/70">
			{page.status === 404 ? 'The requested page was not found.' : 'Your data was not changed.'}
		</p>
		<button class="btn mt-5 btn-primary" onclick={() => window.location.reload()}>Try again</button>
	</div>
</div>
