import type { CategoryOut, ChannelOut, TagOut, UserRead, PlaylistDetailOut } from '$lib/types/api';
import { APIError, createScopedAPI } from '$lib/api';
import { error, redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';
import type { RuntimeMetadata } from '$lib/types/runtime';

const fallbackRuntime: RuntimeMetadata = {
	name: 'ChooseYourTube',
	version: '1.0.0',
	mode: 'full',
	features: {
		registration: true,
		background_jobs: true,
		youtube_oauth: false,
		demo_login: false,
		subscription_imports: true
	}
};

function isPublicAuthRoute(pathname: string): boolean {
	return pathname === '/login' || pathname === '/register';
}

export const load: LayoutLoad = async ({ depends, fetch, url }) => {
	if (isPublicAuthRoute(url.pathname)) {
		return {
			isPublicAuthRoute: true,
			currentUser: null,
			categories: [] as CategoryOut[],
			uncategorizedChannels: [] as ChannelOut[],
			channels: [] as ChannelOut[],
			tags: [] as TagOut[],
			watchLater: null as PlaylistDetailOut | null,
			runtime: fallbackRuntime
		};
	}

	depends('app:folders');
	depends('app:categories');
	depends('app:channels');
	depends('app:tags');
	depends('app:user');

	const response = await fetch('/api/bootstrap');
	if (response.status === 401) {
		await fetch('/api/auth/logout', { method: 'POST' });
		throw redirect(
			307,
			`/login?reason=session_expired&next=${encodeURIComponent(url.pathname + url.search)}`
		);
	}
	if (!response.ok) {
		console.error('Failed to load application bootstrap', response.status);
		throw error(503, 'ChooseYourTube could not load your library. Please retry.');
	}

	const bootstrap = (await response.json()) as {
		current_user: UserRead;
		channels: ChannelOut[];
		tags: TagOut[];
		watch_later: PlaylistDetailOut;
		runtime: RuntimeMetadata;
	};
	let categories: CategoryOut[];
	try {
		categories = await createScopedAPI(fetch).categories.list();
	} catch (cause) {
		if (cause instanceof APIError && cause.status === 401) {
			await fetch('/api/auth/logout', { method: 'POST' });
			throw redirect(
				307,
				`/login?reason=session_expired&next=${encodeURIComponent(url.pathname + url.search)}`
			);
		}
		console.error('Failed to load categories', cause);
		throw error(503, 'ChooseYourTube could not load your library. Please retry.');
	}
	const categorizedChannelIds = new Set(
		categories.flatMap((category) => category.channel_ids ?? [])
	);
	const uncategorizedChannels = bootstrap.channels.filter(
		(channel) => !categorizedChannelIds.has(channel.id)
	);

	return {
		isPublicAuthRoute: false,
		currentUser: bootstrap.current_user,
		categories,
		uncategorizedChannels,
		channels: bootstrap.channels,
		tags: bootstrap.tags,
		watchLater: bootstrap.watch_later,
		runtime: bootstrap.runtime
	};
};
