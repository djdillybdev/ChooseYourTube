import { createScopedAPI, APIError } from '$lib/api';
import type { FolderOut, ChannelOut, TagOut, UserRead } from '$lib/types/api';
import { isRedirect, redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';

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
			tags: [] as TagOut[]
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

		const [folders, tagsResponse] = await Promise.all([
			api.folders.getTree(),
			api.tags.list({ limit: 200 })
		]);
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
			tags: tagsResponse.items
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
			tags: [] as TagOut[]
		};
	}
};
