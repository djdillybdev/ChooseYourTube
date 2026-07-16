<script lang="ts">
	import { getCategoryIcon } from '$lib/icons/categoryIcons';

	interface Props {
		iconKey?: string | null;
		size?: number;
		class?: string;
	}

	let { iconKey = null, size = 20, class: className = '' }: Props = $props();
	const Icon = $derived(getCategoryIcon(iconKey));
</script>

<Icon {size} strokeWidth={1.5} class={className} aria-hidden="true" />
