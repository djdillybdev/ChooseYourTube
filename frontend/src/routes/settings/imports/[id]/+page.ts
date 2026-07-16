import { createScopedAPI } from '$lib/api';
import type { SubscriptionCandidateState } from '$lib/types/api';
import type { PageLoad } from './$types';

const states = new Set(['new', 'selected', 'existing', 'invalid', 'imported', 'failed']);

export const load: PageLoad = async ({ fetch, params, url, parent }) => {
	await parent();
	const rawState = url.searchParams.get('state') ?? 'new';
	const state = states.has(rawState) ? (rawState as SubscriptionCandidateState) : 'new';
	const search = url.searchParams.get('search') ?? undefined;
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = 50;
	const detail = await createScopedAPI(fetch).imports.get(params.id, {
		state,
		search,
		limit: pageSize,
		offset: (page - 1) * pageSize
	});
	return { detail, state, search, page, pageSize };
};
