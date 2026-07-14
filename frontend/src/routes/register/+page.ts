import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import type { RuntimeMetadata } from '$lib/types/runtime';

export const load: PageLoad = async ({ fetch }) => {
	const response = await fetch('/api/meta');
	if (response.ok) {
		const metadata = (await response.json()) as RuntimeMetadata;
		if (!metadata.features.registration) throw redirect(307, '/login');
	}
	return {};
};
