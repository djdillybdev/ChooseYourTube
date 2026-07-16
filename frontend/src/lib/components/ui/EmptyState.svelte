<script lang="ts">
	import { resolve } from '$app/paths';
	interface Props {
		title: string;
		message?: string;
		icon?: 'inbox' | 'folder' | 'search' | 'video';
		actionLabel?: string;
		actionHref?: string;
		onAction?: () => void;
	}

	let { title, message, icon = 'inbox', actionLabel, actionHref, onAction }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center py-12">
	{#if icon === 'inbox'}
		<svg
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
			stroke-width="1.5"
			stroke="currentColor"
			class="mb-4 h-16 w-16 text-base-content/40"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z"
			/>
		</svg>
	{:else if icon === 'folder'}
		<svg
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
			stroke-width="1.5"
			stroke="currentColor"
			class="mb-4 h-16 w-16 text-base-content/40"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
			/>
		</svg>
	{:else if icon === 'search'}
		<svg
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
			stroke-width="1.5"
			stroke="currentColor"
			class="mb-4 h-16 w-16 text-base-content/40"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
			/>
		</svg>
	{:else if icon === 'video'}
		<svg
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
			stroke-width="1.5"
			stroke="currentColor"
			class="mb-4 h-16 w-16 text-base-content/40"
		>
			<path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M15.91 11.672a.375.375 0 010 .656l-5.603 3.113a.375.375 0 01-.557-.328V8.887c0-.286.307-.466.557-.327l5.603 3.112z"
			/>
		</svg>
	{/if}

	<h2 class="mb-2 text-xl font-semibold">{title}</h2>
	{#if message}
		<p class="max-w-lg text-center text-sm text-base-content">{message}</p>
	{/if}
	{#if actionLabel && actionHref}
		<a class="btn mt-4 btn-primary" href={resolve(actionHref as '/inbox')}>{actionLabel}</a>
	{:else if actionLabel && onAction}
		<button class="btn mt-4 btn-primary" type="button" onclick={onAction}>{actionLabel}</button>
	{/if}
</div>
