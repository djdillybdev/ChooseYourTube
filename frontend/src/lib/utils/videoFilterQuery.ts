import type { VideoFilters } from '$lib/types/api';

const ORDER_BY_VALUES = new Set([
	'published_at',
	'title',
	'created_at',
	'duration_seconds',
	'relevance'
]);
const ORDER_DIRECTION_VALUES = new Set(['asc', 'desc']);

export interface VideoFilterQueryState {
	is_watched: boolean | undefined;
	is_short: boolean | undefined;
	channel_id: string | undefined;
	tag_id: string | undefined;
	published_after: string | undefined;
	published_before: string | undefined;
	min_duration_minutes: number | undefined;
	max_duration_minutes: number | undefined;
	order_by: VideoFilters['order_by'];
	order_direction: VideoFilters['order_direction'];
}

interface ParseVideoFilterQueryOptions {
	defaultWatched?: boolean | undefined;
	defaultShort?: boolean | undefined;
	forcedChannelId?: string;
}

export interface ParsedVideoFilterQuery {
	apiFilters: VideoFilters;
	uiFilters: VideoFilterQueryState;
}

function parseBooleanParam(value: string | null): boolean | undefined {
	if (value === 'true') return true;
	if (value === 'false') return false;
	return undefined;
}

function parseDateInput(value: string | null): string | undefined {
	if (!value) return undefined;
	if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return undefined;

	const date = new Date(`${value}T00:00:00.000Z`);
	if (Number.isNaN(date.getTime())) return undefined;

	return value;
}

function parseDurationMinutes(value: string | null): number | undefined {
	if (!value || !/^\d+$/.test(value)) return undefined;

	const minutes = Number(value);
	return Number.isSafeInteger(minutes) && minutes >= 0 && minutes <= 60 ? minutes : undefined;
}

function toStartOfDayISO(value: string): string {
	return new Date(`${value}T00:00:00.000Z`).toISOString();
}

function toEndOfDayISO(value: string): string {
	return new Date(`${value}T23:59:59.999Z`).toISOString();
}

export function parseVideoFilterQuery(
	url: URL,
	options: ParseVideoFilterQueryOptions = {}
): ParsedVideoFilterQuery {
	const q = url.searchParams.get('q') || undefined;

	const watchedParam = url.searchParams.get('is_watched');
	const watchedFromQuery = parseBooleanParam(watchedParam);
	const is_watched =
		watchedParam === 'all'
			? undefined
			: watchedFromQuery !== undefined
				? watchedFromQuery
				: options.defaultWatched;

	const shortParam = url.searchParams.get('is_short');
	const shortFromQuery = parseBooleanParam(shortParam);
	const is_short =
		shortParam === 'all'
			? undefined
			: shortFromQuery !== undefined
				? shortFromQuery
				: (options.defaultShort ?? false);

	const channelFromQuery = url.searchParams.get('channel_id') || undefined;
	const channel_id = options.forcedChannelId ?? channelFromQuery;
	const tag_id = url.searchParams.get('tag_id') || undefined;

	const published_after = parseDateInput(url.searchParams.get('published_after'));
	const published_before = parseDateInput(url.searchParams.get('published_before'));
	let min_duration_minutes = parseDurationMinutes(url.searchParams.get('min_duration_minutes'));
	let max_duration_minutes = parseDurationMinutes(url.searchParams.get('max_duration_minutes'));

	if (
		min_duration_minutes !== undefined &&
		max_duration_minutes !== undefined &&
		min_duration_minutes > max_duration_minutes
	) {
		min_duration_minutes = undefined;
		max_duration_minutes = undefined;
	}

	if (min_duration_minutes === 0) min_duration_minutes = undefined;
	if (max_duration_minutes === 60) max_duration_minutes = undefined;

	const requestedOrderBy = url.searchParams.get('order_by') || undefined;
	const requestedOrderDirection = url.searchParams.get('order_direction') || undefined;

	let order_by: VideoFilters['order_by'] = ORDER_BY_VALUES.has(requestedOrderBy ?? '')
		? (requestedOrderBy as VideoFilters['order_by'])
		: q
			? 'relevance'
			: 'published_at';
	if (order_by === 'relevance' && !q) {
		order_by = 'published_at';
	}

	const order_direction: VideoFilters['order_direction'] = ORDER_DIRECTION_VALUES.has(
		requestedOrderDirection ?? ''
	)
		? (requestedOrderDirection as 'asc' | 'desc')
		: 'desc';

	const apiFilters: VideoFilters = {
		is_watched,
		is_short,
		channel_id,
		tag_id,
		published_after: published_after ? toStartOfDayISO(published_after) : undefined,
		published_before: published_before ? toEndOfDayISO(published_before) : undefined,
		min_duration_seconds:
			min_duration_minutes !== undefined ? min_duration_minutes * 60 : undefined,
		max_duration_seconds:
			max_duration_minutes !== undefined ? max_duration_minutes * 60 : undefined,
		order_by: q ? order_by : order_by === 'relevance' ? undefined : order_by,
		order_direction
	};

	const uiFilters: VideoFilterQueryState = {
		is_watched,
		is_short,
		channel_id,
		tag_id,
		published_after,
		published_before,
		min_duration_minutes,
		max_duration_minutes,
		order_by,
		order_direction
	};

	return { apiFilters, uiFilters };
}
