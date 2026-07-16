<script lang="ts">
	import { resolve } from '$app/paths';
	interface Props {
		message: string;
		heading?: string;
		onRetry?: () => void | Promise<void>;
		retryHref?: string;
		requestId?: string | null;
	}

	let {
		message,
		heading = 'Something went wrong',
		onRetry,
		retryHref,
		requestId = null
	}: Props = $props();
</script>

<div class="flex flex-col items-center justify-center py-12 text-center" role="alert">
	<svg
		xmlns="http://www.w3.org/2000/svg"
		fill="none"
		viewBox="0 0 24 24"
		stroke-width="1.5"
		stroke="currentColor"
		class="mb-4 h-16 w-16 text-error"
	>
		<path
			stroke-linecap="round"
			stroke-linejoin="round"
			d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
		/>
	</svg>

	<h2 class="mb-2 text-xl font-semibold">{heading}</h2>
	<p class="mb-4 max-w-xl text-sm text-base-content/80">{message}</p>
	{#if requestId}<p class="mb-4 text-xs text-base-content/70">Request ID: {requestId}</p>{/if}

	{#if onRetry}
		<button class="btn btn-sm btn-primary" onclick={() => void onRetry()}>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class="h-4 w-4"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
				/>
			</svg>
			Try Again
		</button>
	{:else if retryHref}
		<a class="btn btn-sm btn-primary" href={resolve(retryHref as '/inbox')}>Try again</a>
	{/if}
</div>
