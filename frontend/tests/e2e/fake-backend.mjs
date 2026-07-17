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
let channels = [channel];
let categories = [];
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
let initialSyncPolls = 0;
let failedStatus = 'failed';
const importId = '10000000-0000-0000-0000-000000000001';
const candidateId = '20000000-0000-0000-0000-000000000001';
const importRunId = '30000000-0000-0000-0000-000000000001';
let importStatus = 'ready';
let candidateState = 'new';
let importPolls = 0;

function importDetail(state) {
	const counts = {
		new_count: candidateState === 'new' ? 1 : 0,
		selected_count: candidateState === 'selected' ? 1 : 0,
		imported_count: candidateState === 'imported' ? 1 : 0,
		failed_count: 0
	};
	const candidate = {
		id: candidateId,
		channel_id: 'UC_imported_portfolio1',
		channel_title: 'Imported Portfolio Channel',
		channel_url: 'https://youtube.com/channel/UC_imported_portfolio1',
		state: candidateState,
		source_index: 2,
		message: null
	};
	const items = !state || state === candidateState ? [candidate] : [];
	return {
		import: {
			id: importId,
			source: 'youtube_takeout_csv',
			status: importStatus,
			candidate_count: 1,
			...counts,
			existing_count: 0,
			invalid_count: 0,
			destination_folder_id: null,
			destination_tag_ids: [],
			error_code: null,
			error_message: null,
			created_at: '2026-07-14T10:00:00Z',
			ready_at: '2026-07-14T10:00:00Z',
			queued_at: null,
			started_at: null,
			finished_at: null,
			updated_at: '2026-07-14T10:00:00Z'
		},
		candidates: { total: items.length, items, limit: 50, offset: 0, has_more: false }
	};
}

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
				demo_login: false,
				subscription_imports: true
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
	if (path === '/app/bootstrap')
		return send(response, 200, {
			current_user: {
				id: 'user-1',
				email: 'portfolio@example.com',
				is_active: true,
				is_superuser: false,
				is_verified: true
			},
			folders: [],
			channels,
			tags,
			watch_later: {
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
				total_videos: watchLaterIds.length,
				created_at: '2026-07-14T10:00:00Z',
				video_ids: watchLaterIds
			},
			runtime: {
				name: 'ChooseYourTube',
				version: '0.1.0',
				mode: 'full',
				features: {
					registration: true,
					background_jobs: true,
					youtube_oauth: false,
					demo_login: false,
					subscription_imports: true
				}
			}
		});
	if (path === '/categories' && request.method === 'GET') return send(response, 200, categories);
	if (path === '/categories' && request.method === 'POST') {
		const body = await readBody(request);
		const category = {
			id: `category-${categories.length + 1}`,
			name: String(body.name).trim(),
			icon_key: body.icon_key ?? null,
			created_at: '2026-07-14T10:00:00Z',
			channel_ids: []
		};
		categories = [...categories, category];
		return send(response, 201, category);
	}
	const categoryMatch = path.match(/^\/categories\/(category-\d+)$/);
	if (categoryMatch && request.method === 'GET') {
		const category = categories.find((item) => item.id === categoryMatch[1]);
		return category ? send(response, 200, category) : send(response, 404, {});
	}
	if (categoryMatch && request.method === 'PATCH') {
		const body = await readBody(request);
		categories = categories.map((item) =>
			item.id === categoryMatch[1]
				? {
						...item,
						name: String(body.name).trim(),
						icon_key: 'icon_key' in body ? body.icon_key : item.icon_key
					}
				: item
		);
		return send(
			response,
			200,
			categories.find((item) => item.id === categoryMatch[1])
		);
	}
	if (categoryMatch && request.method === 'DELETE') {
		categories = categories.filter((item) => item.id !== categoryMatch[1]);
		response.writeHead(204);
		return response.end();
	}
	const categoryChannelsMatch = path.match(/^\/categories\/(category-\d+)\/channels$/);
	if (categoryChannelsMatch && request.method === 'PUT') {
		const body = await readBody(request);
		categories = categories.map((item) =>
			item.id === categoryChannelsMatch[1] ? { ...item, channel_ids: body.channel_ids } : item
		);
		return send(
			response,
			200,
			categories.find((item) => item.id === categoryChannelsMatch[1])
		);
	}
	const channelCategoriesMatch = path.match(/^\/categories\/channels\/(.+)$/);
	if (channelCategoriesMatch && request.method === 'PUT') {
		const body = await readBody(request);
		categories = categories.map((item) => ({
			...item,
			channel_ids: body.category_ids.includes(item.id)
				? [...new Set([...item.channel_ids, channelCategoriesMatch[1]])]
				: item.channel_ids.filter((id) => id !== channelCategoriesMatch[1])
		}));
		return send(response, 200, {
			channel_id: channelCategoriesMatch[1],
			category_ids: body.category_ids
		});
	}
	if (path === '/imports/subscriptions/csv' && request.method === 'POST') {
		importStatus = 'ready';
		candidateState = 'new';
		return send(response, 201, importDetail());
	}
	if (path === `/imports/${importId}` && request.method === 'GET')
		return send(response, 200, importDetail(url.searchParams.get('state')));
	if (path === `/imports/${importId}/candidates` && request.method === 'PATCH') {
		const body = await readBody(request);
		candidateState = body.selected ? 'selected' : 'new';
		return send(response, 200, importDetail().import);
	}
	if (path === `/imports/${importId}/commit` && request.method === 'POST') {
		importStatus = 'queued';
		importPolls = 0;
		return send(response, 202, {
			...baseRun,
			id: importRunId,
			kind: 'subscription_import',
			status: 'queued',
			channel_id: null,
			subscription_import_id: importId
		});
	}
	if (path === `/sync-runs/${importRunId}`) {
		importPolls += 1;
		const status = importPolls > 1 ? 'succeeded' : 'running';
		if (status === 'succeeded') {
			importStatus = 'succeeded';
			candidateState = 'imported';
		}
		return send(response, 200, {
			...baseRun,
			id: importRunId,
			kind: 'subscription_import',
			status,
			channel_id: null,
			subscription_import_id: importId,
			items_discovered: 1,
			items_created: status === 'succeeded' ? 1 : 0
		});
	}
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
	if (path === '/channels' && request.method === 'POST') {
		const body = await readBody(request);
		const addedChannel = {
			...channel,
			id: 'UC_added_channel',
			title: 'Added Channel',
			handle: String(body.handle).replace(/^@/, ''),
			folder_id: body.folder_id ?? null
		};
		channels = [...channels.filter((item) => item.id !== addedChannel.id), addedChannel];
		initialSyncPolls = 0;
		return send(response, 201, {
			channel: addedChannel,
			initial_sync: {
				...baseRun,
				id: '00000000-0000-0000-0000-000000000004',
				channel_id: addedChannel.id,
				kind: 'initial_channel_sync',
				status: 'queued'
			}
		});
	}
	if (path === '/channels' && request.method === 'GET')
		return send(response, 200, {
			total: channels.length,
			items: channels,
			limit: 50,
			offset: 0,
			has_more: false
		});
	if (path.startsWith('/channels/') && request.method === 'PATCH') {
		const body = await readBody(request);
		const channelId = path.slice('/channels/'.length);
		const existing = channels.find((item) => item.id === channelId);
		if (!existing) return send(response, 404, {});
		const updated = { ...existing, ...body };
		channels = channels.map((item) => (item.id === channelId ? updated : item));
		return send(response, 200, updated);
	}
	if (path.startsWith('/channels/') && request.method === 'GET') {
		const requestedChannel = channels.find((item) => path === `/channels/${item.id}`);
		if (requestedChannel) return send(response, 200, requestedChannel);
	}
	if (path === '/videos') {
		const minimum = Number(url.searchParams.get('min_duration_seconds') ?? 0);
		const maximum = Number(url.searchParams.get('max_duration_seconds') ?? Infinity);
		const items =
			video.duration_seconds >= minimum && video.duration_seconds <= maximum ? [video] : [];
		return send(response, 200, {
			total: items.length,
			items,
			limit: 24,
			offset: 0,
			has_more: false
		});
	}
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
	if (path === '/sync-runs/00000000-0000-0000-0000-000000000004') {
		initialSyncPolls += 1;
		return send(response, 200, {
			...baseRun,
			id: '00000000-0000-0000-0000-000000000004',
			channel_id: 'UC_added_channel',
			kind: 'initial_channel_sync',
			status: initialSyncPolls > 1 ? 'succeeded' : 'running'
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
