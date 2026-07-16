<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import type { CategoryOut, ChannelOut } from '$lib/types/api';
	import { categoryExpansion } from '$lib/stores/categoryExpansion.svelte';
	import ChannelTreeItem from './ChannelTreeItem.svelte';
	import CategoryIcon from '$lib/components/ui/CategoryIcon.svelte';

	interface Props {
		category?: CategoryOut;
		label?: string;
		channels: ChannelOut[];
	}

	let { category, label = 'Uncategorized', channels }: Props = $props();
	const expansionId = $derived(category?.id ?? '__uncategorized__');
	const isExpanded = $derived(categoryExpansion.isExpanded(expansionId));
	const isActive = $derived(category ? page.url.pathname === `/categories/${category.id}` : false);

	function toggleExpand(event: MouseEvent) {
		event.preventDefault();
		event.stopPropagation();
		categoryExpansion.toggle(expansionId);
	}
</script>

<li>
	<div class="flex items-center">
		{#if channels.length > 0}
			<button
				onclick={toggleExpand}
				class="btn mr-1 p-0 btn-ghost btn-xs hover:bg-transparent"
				aria-label={isExpanded
					? `Collapse ${category?.name ?? label}`
					: `Expand ${category?.name ?? label}`}
			>
				<svg
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					class="h-4 w-4 transition-transform"
					class:rotate-90={isExpanded}
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
				</svg>
			</button>
		{:else}
			<span class="mr-1 w-4"></span>
		{/if}

		{#if category}
			<a
				href={resolve('/categories/[id]', { id: category.id })}
				class="flex flex-1 items-center gap-2 rounded px-2 py-1.5 transition-colors"
				class:bg-base-200={isActive}
			>
				<CategoryIcon iconKey={category.icon_key} class="h-5 w-5 shrink-0" />
				<span class="text-sm">{category.name}</span>
			</a>
		{:else}
			<span class="flex flex-1 items-center gap-2 px-2 py-1.5 text-sm text-base-content/70">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="1.5"
						d="M9.568 3.75h4.864c1.336 0 2.591.638 3.38 1.717l2.505 3.423a4.2 4.2 0 010 4.96l-2.505 3.423a4.2 4.2 0 01-3.38 1.717H9.568a4.2 4.2 0 01-3.38-1.717L3.683 13.85a4.2 4.2 0 010-4.96l2.505-3.423a4.2 4.2 0 013.38-1.717z"
					/>
				</svg>
				{label}
			</span>
		{/if}
	</div>

	{#if channels.length > 0 && isExpanded}
		<ul class="mt-1">
			{#each channels as channel (channel.id)}
				<ChannelTreeItem {channel} depth={1} />
			{/each}
		</ul>
	{/if}
</li>
