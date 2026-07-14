<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

<div class="container mx-auto max-w-6xl p-6 pb-0">
	<h1 class="text-3xl font-bold">Settings</h1>
	<p class="text-base-content/60">Manage organization, imports, and background activity.</p>
	<div role="tablist" class="tabs-border mt-5 tabs">
		<a
			role="tab"
			class="tab"
			class:tab-active={page.url.pathname.startsWith('/settings/imports')}
			href={resolve('/settings/imports')}>Imports</a
		>
		<a
			role="tab"
			class="tab"
			class:tab-active={page.url.pathname === '/settings'}
			href={resolve('/settings')}>Organization</a
		>
		<a
			role="tab"
			class="tab"
			class:tab-active={page.url.pathname.startsWith('/settings/sync')}
			href={resolve('/settings/sync')}>Sync Activity</a
		>
		<a
			role="tab"
			class="tab"
			class:tab-active={page.url.pathname.startsWith('/settings/account')}
			href={resolve('/settings/account')}>Account</a
		>
	</div>
</div>

{@render children()}
