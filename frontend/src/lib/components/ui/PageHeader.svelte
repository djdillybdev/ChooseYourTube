<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		description?: string;
		actions?: Snippet;
	}

	let { title, description, actions }: Props = $props();
</script>

<header class="mb-6 flex min-w-0 flex-wrap items-start justify-between gap-3">
	<div class="min-w-0">
		<h1 class="text-2xl leading-tight font-bold break-words sm:text-3xl">{title}</h1>
		{#if description}<p class="mt-1 text-sm text-base-content">{description}</p>{/if}
	</div>
	{#if actions}<div class="flex flex-wrap items-center gap-2">{@render actions()}</div>{/if}
</header>
