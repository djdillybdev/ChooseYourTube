<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';

	interface Props {
		total: number;
		currentPage: number;
		pageSize: number;
		basePath: string;
	}

	let { total, currentPage, pageSize, basePath }: Props = $props();

	let totalPages = $derived(Math.max(1, Math.ceil(total / pageSize)));

	function navigateTo(page: number, size: number = pageSize) {
		const url = new URL(window.location.href);
		url.searchParams.set('page', String(page));
		url.searchParams.set('pageSize', String(size));
		// Preserves search param (and any other params)
		goto(resolve(`${basePath}${url.search}` as '/inbox'));
	}

	/** Sliding window of up to 5 page numbers centred on currentPage */
	let visiblePages = $derived.by(() => {
		const WIN = 5;
		let start = Math.max(1, currentPage - Math.floor(WIN / 2));
		let end = Math.min(totalPages, start + WIN - 1);
		start = Math.max(1, end - WIN + 1);
		const out: number[] = [];
		for (let i = start; i <= end; i++) out.push(i);
		return out;
	});
</script>

{#if total > 0}
	<nav class="flex items-center justify-between pt-6 pb-2">
		<!-- Page buttons -->
		{#if totalPages >= 1}
			<div class="flex items-center gap-1">
				<!-- Prev -->
				<button
					class="btn btn-square btn-ghost btn-sm"
					disabled={currentPage <= 1}
					onclick={() => navigateTo(currentPage - 1)}
					aria-label="Previous page"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						class="h-4 w-4"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
					</svg>
				</button>

				<!-- First + ellipsis -->
				{#if visiblePages[0] > 1}
					<button class="btn btn-square btn-ghost btn-sm" onclick={() => navigateTo(1)}>1</button>
					{#if visiblePages[0] > 2}
						<span class="px-1 text-base-content/40">…</span>
					{/if}
				{/if}

				<!-- Visible range -->
				{#each visiblePages as p (p)}
					<button
						class="btn btn-square btn-ghost btn-sm"
						class:btn-primary={p === currentPage}
						onclick={() => navigateTo(p)}>{p}</button
					>
				{/each}

				<!-- Ellipsis + last -->
				{#if visiblePages[visiblePages.length - 1] < totalPages}
					{#if visiblePages[visiblePages.length - 1] < totalPages - 1}
						<span class="px-1 text-base-content/40">…</span>
					{/if}
					<button class="btn btn-square btn-ghost btn-sm" onclick={() => navigateTo(totalPages)}
						>{totalPages}</button
					>
				{/if}

				<!-- Next -->
				<button
					class="btn btn-square btn-ghost btn-sm"
					disabled={currentPage >= totalPages}
					onclick={() => navigateTo(currentPage + 1)}
					aria-label="Next page"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						class="h-4 w-4"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
					</svg>
				</button>
			</div>
		{:else}
			<div></div>
			<!-- spacer so page-size selector stays right-aligned -->
		{/if}

		<!-- Page-size selector (always visible when there are results) -->
		<div class="flex items-center gap-2 text-sm">
			<span class="text-base-content/60">Per page:</span>
			<select
				class="select-bordered select select-sm"
				value={pageSize}
				onchange={(e) => navigateTo(1, Number((e.target as HTMLSelectElement).value))}
			>
				{#each [12, 24, 48, 100] as size (size)}
					<option value={size}>{size}</option>
				{/each}
			</select>
		</div>
	</nav>
{/if}
