<script lang="ts">
	import CategoryIcon from './CategoryIcon.svelte';
	import { CATEGORY_ICONS, hasCategoryIcon } from '$lib/icons/categoryIcons';

	interface Props {
		value?: string | null;
		disabled?: boolean;
		onChange: (value: string | null) => void;
	}

	let { value = null, disabled = false, onChange }: Props = $props();
	let query = $state('');
	const normalizedQuery = $derived(query.trim().toLocaleLowerCase());
	const filteredIcons = $derived(
		CATEGORY_ICONS.filter(
			(icon) =>
				!normalizedQuery ||
				icon.label.toLocaleLowerCase().includes(normalizedQuery) ||
				icon.key.includes(normalizedQuery)
		)
	);
</script>

<fieldset {disabled}>
	<legend class="label-text mb-2">Icon</legend>
	<label class="input-bordered input mb-2 flex w-full items-center gap-2">
		<span class="sr-only">Search icons</span>
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-4 w-4" aria-hidden="true">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="1.5"
				d="m21 21-4.35-4.35m2.35-5.65a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z"
			/>
		</svg>
		<input bind:value={query} placeholder="Search icons" class="grow" />
	</label>

	<div
		class="grid max-h-52 grid-cols-6 gap-1 overflow-y-auto rounded border border-base-300 p-2 sm:grid-cols-8"
		role="radiogroup"
		aria-label="Category icon"
	>
		<button
			type="button"
			class="btn btn-square btn-sm"
			class:btn-primary={!hasCategoryIcon(value)}
			class:btn-ghost={hasCategoryIcon(value)}
			role="radio"
			aria-checked={!hasCategoryIcon(value)}
			aria-label="Default icon"
			title="Default icon"
			onclick={() => onChange(null)}
		>
			<CategoryIcon />
		</button>
		{#each filteredIcons as icon (icon.key)}
			<button
				type="button"
				class="btn btn-square btn-sm"
				class:btn-primary={value === icon.key}
				class:btn-ghost={value !== icon.key}
				role="radio"
				aria-checked={value === icon.key}
				aria-label={icon.label}
				title={icon.label}
				onclick={() => onChange(icon.key)}
			>
				<CategoryIcon iconKey={icon.key} />
			</button>
		{/each}
	</div>
	{#if filteredIcons.length === 0}
		<p class="mt-2 text-sm text-base-content/60">No icons match “{query.trim()}”.</p>
	{/if}
</fieldset>
