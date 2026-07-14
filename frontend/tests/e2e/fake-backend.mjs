import { createServer } from 'node:http';

const channel = {
	id: 'UC_portfolio',
	title: 'Portfolio Channel',
	handle: 'portfolio',
	description: null,
	thumbnail_url: null,
	is_favorited: false,
	folder_id: null,
	created_at: '2026-07-14T10:00:00Z',
	last_updated: '2026-07-14T10:00:00Z',
	total_videos: 0,
	latest_sync: null
};
const baseRun = {
	owner_id: 'user-1',
	channel_id: channel.id,
	subscription_import_id: null,
	attempt_count: 1,
	max_attempts: 4,
	items_discovered: 0,
	items_created: 0,
	items_updated: 0,
	items_skipped: 0,
	items_failed: 0,
	error_code: null,
	error_message: null,
	retryable: false,
	queued_at: '2026-07-14T10:00:00Z',
	started_at: null,
	finished_at: null,
	next_retry_at: null,
	created_at: '2026-07-14T10:00:00Z',
	updated_at: '2026-07-14T10:00:00Z'
};
let refreshPolls = 0;
let failedStatus = 'failed';

function send(response, status, payload) {
	response.writeHead(status, { 'content-type': 'application/json' });
	response.end(JSON.stringify(payload));
}

createServer((request, response) => {
	const url = new URL(request.url ?? '/', 'http://127.0.0.1:8123');
	const path = url.pathname.replace(/\/$/, '') || '/';
	if (path === '/')
		return send(response, 200, {
			name: 'ChooseYourTube API',
			version: '0.1.0',
			mode: 'full',
			features: {
				registration: true,
				background_jobs: true,
				youtube_oauth: false,
				demo_login: false
			}
		});
	if (path === '/auth/session/login')
		return send(response, 200, {
			access_token: 'e2e-access',
			refresh_token: 'e2e-refresh',
			token_type: 'bearer'
		});
	if (path === '/users/me')
		return send(response, 200, {
			id: 'user-1',
			email: 'portfolio@example.com',
			is_active: true,
			is_superuser: false,
			is_verified: true
		});
	if (path === '/folders/tree') return send(response, 200, []);
	if (path === '/tags')
		return send(response, 200, { total: 0, items: [], limit: 200, offset: 0, has_more: false });
	if (path === '/channels')
		return send(response, 200, {
			total: 1,
			items: [channel],
			limit: 50,
			offset: 0,
			has_more: false
		});
	if (path === `/channels/${channel.id}` && request.method === 'GET')
		return send(response, 200, channel);
	if (path === '/videos')
		return send(response, 200, { total: 0, items: [], limit: 24, offset: 0, has_more: false });
	if (path === `/channels/${channel.id}/refresh` && request.method === 'POST') {
		refreshPolls = 0;
		return send(response, 202, {
			...baseRun,
			id: '00000000-0000-0000-0000-000000000001',
			kind: 'channel_refresh',
			status: 'queued'
		});
	}
	if (path === '/sync-runs/00000000-0000-0000-0000-000000000001') {
		refreshPolls += 1;
		const status = refreshPolls > 1 ? 'succeeded' : 'running';
		return send(response, 200, {
			...baseRun,
			id: '00000000-0000-0000-0000-000000000001',
			kind: 'channel_refresh',
			status
		});
	}
	if (path === '/sync-runs/quota')
		return send(response, 200, {
			date: '2026-07-14',
			budget: 8000,
			estimated_units_used: 12,
			estimated_units_remaining: 7988,
			call_count: 12,
			exhausted: false
		});
	if (path === '/sync-runs' && request.method === 'GET') {
		const retryable = failedStatus === 'failed';
		return send(response, 200, {
			total: 1,
			limit: 20,
			offset: 0,
			has_more: false,
			items: [
				{
					...baseRun,
					id: '00000000-0000-0000-0000-000000000002',
					kind: 'playlist_sync',
					status: failedStatus,
					error_code: retryable ? 'RSS_FETCH_FAILED' : null,
					error_message: retryable ? 'The channel feed is temporarily unavailable.' : null,
					retryable
				}
			]
		});
	}
	if (
		path === '/sync-runs/00000000-0000-0000-0000-000000000002/retry' &&
		request.method === 'POST'
	) {
		failedStatus = 'queued';
		return send(response, 202, {
			...baseRun,
			id: '00000000-0000-0000-0000-000000000003',
			kind: 'playlist_sync',
			status: 'queued'
		});
	}
	return send(response, 404, {
		code: 'NOT_FOUND',
		message: 'Not found',
		request_id: 'e2e',
		retryable: false
	});
}).listen(8123, '127.0.0.1');
