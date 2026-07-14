<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';

	onMount(() => {
		goto(resolve('/inbox'), { replaceState: true });
	});
</script>

<!-- Loading state while redirecting -->
<div class="flex h-screen items-center justify-center">
	<span class="loading loading-lg loading-spinner"></span>
</div>
