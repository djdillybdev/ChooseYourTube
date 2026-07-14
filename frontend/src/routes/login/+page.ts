import type { PageLoad } from './$types';
import type { RuntimeMetadata } from '$lib/types/runtime';

export const load: PageLoad = async ({ fetch }) => {
	const response = await fetch('/api/meta');
	const metadata = response.ok ? ((await response.json()) as RuntimeMetadata) : null;
	return { metadata };
};
