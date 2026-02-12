<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		goto('/inbox', { replaceState: true });
	});
</script>

<!-- Loading state while redirecting -->
<div class="flex h-screen items-center justify-center">
	<span class="loading loading-lg loading-spinner"></span>
</div>
