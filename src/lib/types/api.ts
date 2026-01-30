// TypeScript types generated from OpenAPI specification

// ===== Core Entity Types =====

export interface ChannelOut {
	id: string;
	title: string;
	handle: string | null;
	description: string | null;
	thumbnail_url: string | null;
	is_favorited: boolean;
	folder_id: number | null;
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
	id: number;
	name: string;
	parent_id: number | null;
	children: FolderOut[];
}

export interface TagOut {
	id: number;
	name: string;
	created_at: string;
}

// ===== Create/Update Schemas =====

export interface ChannelCreate {
	handle: string;
	folder_id?: number;
}

export interface ChannelUpdate {
	is_favorited?: boolean;
	folder_id?: number | null;
	tag_ids?: number[];
}

export interface VideoUpdate {
	is_favorited?: boolean;
	is_watched?: boolean;
	is_short?: boolean;
	tag_ids?: number[];
}

export interface FolderCreate {
	name: string;
	parent_id?: number;
}

export interface FolderUpdate {
	name?: string;
	parent_id?: number | null;
}

export interface TagCreate {
	name: string;
}

export interface TagUpdate {
	name: string;
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
	tag_id?: number;
	published_after?: string;
	published_before?: string;
	limit?: number;
	offset?: number;
}

export interface ChannelFilters extends Record<string, unknown> {
	is_favorited?: boolean;
	folder_id?: number;
	tag_id?: number;
	limit?: number;
	offset?: number;
}

export interface TagFilters extends Record<string, unknown> {
	limit?: number;
	offset?: number;
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
