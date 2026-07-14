import { createScopedAPI } from '$lib/api';
import type { SyncRunKind, SyncRunStatus } from '$lib/types/api';
import type { PageLoad } from './$types';

const statuses = new Set(['queued', 'running', 'succeeded', 'partial', 'failed']);
const kinds = new Set([
	'initial_channel_sync',
	'channel_refresh',
	'playlist_sync',
	'subscription_import',
	'demo_maintenance'
]);

export const load: PageLoad = async ({ fetch, url }) => {
	const api = createScopedAPI(fetch);
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const pageSize = 20;
	const rawStatus = url.searchParams.get('status');
	const rawKind = url.searchParams.get('kind');
	const status = rawStatus && statuses.has(rawStatus) ? (rawStatus as SyncRunStatus) : undefined;
	const kind = rawKind && kinds.has(rawKind) ? (rawKind as SyncRunKind) : undefined;
	const [runs, quota] = await Promise.all([
		api.syncRuns.list({ status, kind, limit: pageSize, offset: (page - 1) * pageSize }),
		api.syncRuns.quota()
	]);
	return { runs, quota, page, pageSize, status, kind };
};
