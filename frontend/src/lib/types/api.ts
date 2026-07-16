import type { components } from './generated';

type Schemas = components['schemas'];

export type APIErrorBody = Schemas['APIErrorBody'];
export type ChannelOut = Schemas['ChannelOut'];
export type VideoOut = Schemas['VideoOut'];
export type FolderOut = Schemas['FolderOut'];
export type CategoryOut = Schemas['CategoryOut'];
export type TagOut = Schemas['TagOut'];
export type PlaylistOut = Schemas['PlaylistOut'];
export type PlaylistDetailOut = Schemas['PlaylistDetailOut'];
export type ChannelPlaylistOut = Schemas['ChannelPlaylistOut'];
export type UserRead = Schemas['UserRead'];
export type SyncRunOut = Schemas['SyncRunOut'];
export type LatestSyncSummary = Schemas['LatestSyncSummary'];
export type YouTubeQuotaStatusOut = Schemas['YouTubeQuotaStatusOut'];
export type SubscriptionImportOut = Schemas['SubscriptionImportOut'];
export type SubscriptionImportCandidateOut = Schemas['SubscriptionImportCandidateOut'];
export type SubscriptionImportDetailOut = Schemas['SubscriptionImportDetailOut'];
export type OAuthStartOut = Schemas['OAuthStartOut'];
export type SubscriptionCandidateState = Schemas['SubscriptionCandidateState'];

export type ChannelCreate = Schemas['ChannelCreate'];
export type ChannelUpdate = Schemas['ChannelUpdate'];
export type VideoUpdate = Schemas['VideoUpdate'];
export type FolderCreate = Schemas['FolderCreate'];
export type FolderUpdate = Schemas['FolderUpdate'];
export type CategoryCreate = Schemas['CategoryCreate'];
export type CategoryUpdate = Schemas['CategoryUpdate'];
export type CategoryChannelsUpdate = Schemas['CategoryChannelsUpdate'];
export type ChannelCategoriesUpdate = Schemas['ChannelCategoriesUpdate'];
export type ChannelCategoriesOut = Schemas['ChannelCategoriesOut'];
export type TagCreate = Schemas['TagCreate'];
export type TagUpdate = Schemas['TagUpdate'];
export type PlaylistCreate = Omit<Schemas['PlaylistCreate'], 'is_system'> & {
	is_system?: boolean;
};
export type PlaylistUpdate = Schemas['PlaylistUpdate'];
export type PlaylistSetVideos = Schemas['PlaylistSetVideos'];
export type PlaylistAddVideo = Schemas['PlaylistAddVideo'];
export type PlaylistAddVideos = Schemas['PlaylistAddVideos'];
export type PlaylistMoveVideo = Schemas['PlaylistMoveVideo'];
export type PlaylistSetPosition = Schemas['PlaylistSetPosition'];
export type CandidateSelectionUpdate = Schemas['CandidateSelectionUpdate'];
export type SubscriptionImportCommit = Schemas['SubscriptionImportCommit'];

export interface PaginatedResponse<T> {
	total: number;
	items: T[];
	limit: number;
	offset: number;
	has_more: boolean;
}

export interface VideoFilters extends Record<string, unknown> {
	is_watched?: boolean;
	is_short?: boolean;
	channel_id?: string;
	video_ids?: string;
	tag_id?: string;
	published_after?: string;
	published_before?: string;
	limit?: number;
	offset?: number;
	q?: string;
	order_by?: 'published_at' | 'title' | 'created_at' | 'duration_seconds' | 'relevance';
	order_direction?: 'asc' | 'desc';
}

export interface ChannelFilters extends Record<string, unknown> {
	is_favorited?: boolean;
	folder_id?: string;
	tag_id?: string;
	limit?: number;
	offset?: number;
}

export interface TagFilters extends Record<string, unknown> {
	limit?: number;
	offset?: number;
}

export interface PlaylistFilters extends Record<string, unknown> {
	limit?: number;
	offset?: number;
	is_system?: boolean | null;
}

export interface ChannelPlaylistFilters extends Record<string, unknown> {
	include_inactive?: boolean;
	limit?: number;
	offset?: number;
}

export type SyncRunKind =
	| 'initial_channel_sync'
	| 'channel_refresh'
	| 'playlist_sync'
	| 'subscription_import'
	| 'demo_maintenance';

export type SyncRunStatus = 'queued' | 'running' | 'succeeded' | 'partial' | 'failed';

export interface SyncRunFilters extends Record<string, unknown> {
	status?: SyncRunStatus;
	kind?: SyncRunKind;
	channel_id?: string;
	limit?: number;
	offset?: number;
}

const KNOWN_MESSAGES: Record<string, string> = {
	FEATURE_DISABLED: 'This feature is not available in the current application mode.',
	FEATURE_DISABLED_IN_DEMO:
		'Live refresh is disabled in the recruiter demo. Its sample data is maintained daily.',
	YOUTUBE_QUOTA_EXHAUSTED:
		'YouTube refresh is paused because the daily API quota has been reached.',
	QUEUE_UNAVAILABLE: 'Synchronization is temporarily unavailable. Please try again shortly.',
	UNAUTHENTICATED: 'Please log in to continue.',
	FORBIDDEN: 'You do not have permission to perform this action.',
	NOT_FOUND: 'The requested item could not be found.',
	VALIDATION_ERROR: 'Please check the submitted information and try again.'
};

export class APIError extends Error {
	readonly code: string;
	readonly requestId: string | null;
	readonly retryable: boolean;

	constructor(
		public readonly status: number,
		body: Partial<APIErrorBody> | unknown
	) {
		const error = body && typeof body === 'object' ? (body as Partial<APIErrorBody>) : {};
		const code = typeof error.code === 'string' ? error.code : 'REQUEST_FAILED';
		const requestId = typeof error.request_id === 'string' ? error.request_id : null;
		const safeMessage =
			KNOWN_MESSAGES[code] ??
			(typeof error.message === 'string' ? error.message : 'The request could not be completed.');
		super(requestId ? `${safeMessage} Request ID: ${requestId}` : safeMessage);
		this.name = 'APIError';
		this.code = code;
		this.requestId = requestId;
		this.retryable = error.retryable === true;
	}
}
