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
	latest_sync: null,
	tag_ids: []
};
const video = {
	id: 'phase3video',
	channel_id: channel.id,
	title: 'Phase 3 portfolio video',
	description: 'Organization workflow fixture',
	thumbnail_url: null,
	published_at: '2026-07-14T09:00:00Z',
	duration_seconds: 180,
	yt_tags: [],
	is_short: false,
	is_favorited: false,
	is_watched: false,
	created_at: '2026-07-14T09:00:00Z',
	tag_ids: []
};
let watchLaterIds = [];
let tags = [];
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

async function readBody(request) {
	const chunks = [];
	for await (const chunk of request) chunks.push(chunk);
	return chunks.length ? JSON.parse(Buffer.concat(chunks).toString('utf8')) : {};
}

createServer(async (request, response) => {
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
	if (path === '/tags' && request.method === 'GET')
		return send(response, 200, {
			total: tags.length,
			items: tags,
			limit: 200,
			offset: 0,
			has_more: false
		});
	if (path === '/tags' && request.method === 'POST') {
		const body = await readBody(request);
		const tag = {
			id: 'tag-e2e',
			name: String(body.name).trim().toLowerCase(),
			created_at: '2026-07-14T10:00:00Z',
			channel_count: 0,
			video_count: 0
		};
		tags = [tag];
		return send(response, 201, tag);
	}
	if (path === '/tags/tag-e2e' && request.method === 'PATCH') {
		const body = await readBody(request);
		tags = tags.map((tag) => ({ ...tag, name: String(body.name).trim().toLowerCase() }));
		return send(response, 200, tags[0]);
	}
	if (path === '/tags/tag-e2e' && request.method === 'DELETE') {
		tags = [];
		response.writeHead(204);
		return response.end();
	}
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
		return send(response, 200, { total: 1, items: [video], limit: 24, offset: 0, has_more: false });
	if (path === `/videos/${video.id}`) return send(response, 200, video);
	if (path === '/playlists/watch-later' && request.method === 'GET')
		return send(response, 200, {
			id: 'watch-later-e2e',
			name: 'Watch Later',
			description: 'Videos saved to watch later',
			thumbnail_url: null,
			is_system: true,
			system_key: 'watch_later',
			source_type: 'manual',
			source_channel_id: null,
			source_youtube_playlist_id: null,
			source_is_active: true,
			source_last_synced_at: null,
			current_position: null,
			total_videos: watchLaterIds.length,
			created_at: '2026-07-14T10:00:00Z',
			video_ids: watchLaterIds
		});
	if (path === `/playlists/watch-later/videos/${video.id}` && request.method === 'PUT') {
		watchLaterIds = [video.id];
		return send(response, 200, {
			id: 'watch-later-e2e',
			name: 'Watch Later',
			description: null,
			thumbnail_url: null,
			is_system: true,
			system_key: 'watch_later',
			source_type: 'manual',
			source_channel_id: null,
			source_youtube_playlist_id: null,
			source_is_active: true,
			source_last_synced_at: null,
			current_position: null,
			total_videos: 1,
			created_at: '2026-07-14T10:00:00Z',
			video_ids: watchLaterIds
		});
	}
	if (path === `/playlists/watch-later/videos/${video.id}` && request.method === 'DELETE') {
		watchLaterIds = [];
		response.writeHead(204);
		return response.end();
	}
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
