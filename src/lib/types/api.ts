// TypeScript types generated from OpenAPI specification

// ===== Core Entity Types =====

export interface ChannelOut {
	id: string;
	title: string;
	handle: string | null;
	description: string | null;
	thumbnail_url: string | null;
	is_favorited: boolean;
	folder_id: string | null;
	created_at: string;
	last_updated: string;
	total_videos: number;
}

export interface VideoOut {
	id: string;
	channel_id: string;
	title: string;
	description: string | null;
	thumbnail_url: string | null;
	published_at: string;
	duration_seconds: number | null;
	yt_tags: string[];
	is_short: boolean;
	is_favorited: boolean;
	is_watched: boolean;
	created_at: string;
}

export interface FolderOut {
	id: string;
	name: string;
	parent_id: string | null;
	position: number;
	children: FolderOut[];
}

export interface TagOut {
	id: string;
	name: string;
	created_at: string;
}

export interface PlaylistOut {
	id: string;
	name: string;
	description: string | null;
	is_system: boolean;
	created_at: string;
}

export interface PlaylistDetailOut extends PlaylistOut {
	current_position: number | null;
	total_videos: number;
	video_ids: string[];
}

// ===== Create/Update Schemas =====

export interface ChannelCreate {
	handle: string;
	folder_id?: string;
}

export interface ChannelUpdate {
	is_favorited?: boolean;
	folder_id?: string | null;
	tag_ids?: string[];
}

export interface VideoUpdate {
	is_favorited?: boolean;
	is_watched?: boolean;
	is_short?: boolean;
	tag_ids?: string[];
}

export interface FolderCreate {
	name: string;
	parent_id?: string | null;
	position?: number | null;
}

export interface FolderUpdate {
	name?: string;
	parent_id?: string | null;
	position?: number | null;
}

export interface TagCreate {
	name: string;
}

export interface TagUpdate {
	name: string;
}

export interface PlaylistCreate {
	name: string;
	description?: string | null;
	is_system?: boolean;
}

export interface PlaylistUpdate {
	name?: string | null;
	description?: string | null;
}

export interface PlaylistSetVideos {
	video_ids: string[];
}

export interface PlaylistAddVideo {
	video_id: string;
	position?: number | null;
}

export interface PlaylistAddVideos {
	video_ids: string[];
	position?: number | null;
}

export interface PlaylistMoveVideo {
	video_id: string;
	new_position: number;
}

export interface PlaylistSetPosition {
	current_position?: number | null;
}

// ===== Pagination =====

export interface PaginatedResponse<T> {
	total: number;
	items: T[];
	limit: number;
	offset: number;
	has_more: boolean;
}

// ===== Filter Types =====

export interface VideoFilters extends Record<string, unknown> {
	is_favorited?: boolean;
	is_watched?: boolean;
	is_short?: boolean;
	channel_id?: string;
	tag_id?: string;
	published_after?: string;
	published_before?: string;
	limit?: number;
	offset?: number;
	q?: string;
	order_by?: string;
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

// ===== Error Handling =====

export class APIError extends Error {
	constructor(
		public status: number,
		public detail: unknown
	) {
		super(`API Error ${status}`);
		this.name = 'APIError';
	}
}

// ===== HTTP Validation Error (from OpenAPI spec) =====

export interface ValidationError {
	loc: (string | number)[];
	msg: string;
	type: string;
}

export interface HTTPValidationError {
	detail?: ValidationError[];
}
