import { createScopedAPI, APIError } from '$lib/api';
import type { FolderOut, ChannelOut, TagOut, UserRead, PlaylistDetailOut } from '$lib/types/api';
import { isRedirect, redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';
import type { RuntimeMetadata } from '$lib/types/runtime';

const fallbackRuntime: RuntimeMetadata = {
	name: 'ChooseYourTube',
	version: '0.1.0',
	mode: 'full',
	features: { registration: true, background_jobs: true, youtube_oauth: false, demo_login: false }
};

function isPublicAuthRoute(pathname: string): boolean {
	return pathname === '/login' || pathname === '/register';
}

export const load: LayoutLoad = async ({ depends, fetch, url }) => {
	if (isPublicAuthRoute(url.pathname)) {
		return {
			isPublicAuthRoute: true,
			currentUser: null,
			folders: [] as FolderOut[],
			unfolderedChannels: [] as ChannelOut[],
			channels: [] as ChannelOut[],
			tags: [] as TagOut[],
			watchLater: null as PlaylistDetailOut | null,
			runtime: fallbackRuntime
		};
	}

	depends('app:folders');
	depends('app:channels');
	depends('app:tags');
	depends('app:user');

	const api = createScopedAPI(fetch);

	try {
		const meResponse = await fetch('/api/auth/me');
		if (meResponse.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}
		if (!meResponse.ok) {
			throw new Error('Failed to load current user');
		}
		const currentUser = (await meResponse.json()) as UserRead;

		const [folders, tagsResponse, metadataResponse, watchLater] = await Promise.all([
			api.folders.getTree(),
			api.tags.list({ limit: 200 }),
			fetch('/api/meta'),
			api.playlists.getWatchLater()
		]);
		const runtime = metadataResponse.ok
			? ((await metadataResponse.json()) as RuntimeMetadata)
			: fallbackRuntime;
		const channels = [];

		let channelsResponse = await api.channels.list();
		do {
			for (const channel of channelsResponse.items) {
				channels.push(channel);
			}
			channelsResponse = await api.channels.list({
				limit: channelsResponse.limit,
				offset: channelsResponse.offset + channelsResponse.limit
			});
		} while (channelsResponse.has_more);
		const unfolderedChannels: ChannelOut[] = channels.filter(
			(channel) => channel.folder_id === null
		);
		return {
			isPublicAuthRoute: false,
			currentUser,
			folders,
			unfolderedChannels,
			channels,
			tags: tagsResponse.items,
			watchLater,
			runtime
		};
	} catch (error) {
		if (isRedirect(error)) {
			throw error;
		}
		if (error instanceof APIError && error.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
		}

		console.error('Failed to load data:', error);
		return {
			isPublicAuthRoute: false,
			currentUser: null,
			folders: [] as FolderOut[],
			unfolderedChannels: [] as ChannelOut[],
			channels: [] as ChannelOut[],
			tags: [] as TagOut[],
			watchLater: null as PlaylistDetailOut | null,
			runtime: fallbackRuntime
		};
	}
};
