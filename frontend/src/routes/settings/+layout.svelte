<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	function isCurrent(path: string, exact = false): boolean {
		return exact ? page.url.pathname === path : page.url.pathname.startsWith(path);
	}
</script>

<div class="container mx-auto max-w-6xl p-6 pb-0">
	<h1 class="text-3xl font-bold">Settings</h1>
	<p class="text-base-content">Manage organization, imports, and background activity.</p>
	<nav
		class="tabs-border mt-5 tabs overflow-x-auto whitespace-nowrap"
		aria-label="Settings sections"
	>
		<a
			class="tab text-base-content"
			class:tab-active={isCurrent('/settings/appearance')}
			aria-current={isCurrent('/settings/appearance') ? 'page' : undefined}
			href={resolve('/settings/appearance')}>Appearance</a
		>
		<a
			class="tab text-base-content"
			class:tab-active={isCurrent('/settings/imports')}
			aria-current={isCurrent('/settings/imports') ? 'page' : undefined}
			href={resolve('/settings/imports')}>Imports</a
		>
		<a
			class="tab text-base-content"
			class:tab-active={isCurrent('/settings', true)}
			aria-current={isCurrent('/settings', true) ? 'page' : undefined}
			href={resolve('/settings')}>Organization</a
		>
		<a
			class="tab text-base-content"
			class:tab-active={isCurrent('/settings/sync')}
			aria-current={isCurrent('/settings/sync') ? 'page' : undefined}
			href={resolve('/settings/sync')}>Sync Activity</a
		>
		<a
			class="tab text-base-content"
			class:tab-active={isCurrent('/settings/account')}
			aria-current={isCurrent('/settings/account') ? 'page' : undefined}
			href={resolve('/settings/account')}>Account</a
		>
	</nav>
</div>

{@render children()}
