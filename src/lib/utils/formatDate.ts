/**
 * Format a date string to relative time (e.g., "2 hours ago", "3 days ago")
 * @param dateStr - ISO 8601 date string
 * @returns Relative time string
 */
export function formatRelativeDate(dateStr: string): string {
	const date = new Date(dateStr);
	const now = new Date();
	const diffMs = now.getTime() - date.getTime();
	const diffSeconds = Math.floor(diffMs / 1000);
	const diffMinutes = Math.floor(diffSeconds / 60);
	const diffHours = Math.floor(diffMinutes / 60);
	const diffDays = Math.floor(diffHours / 24);
	const diffWeeks = Math.floor(diffDays / 7);
	const diffMonths = Math.floor(diffDays / 30);
	const diffYears = Math.floor(diffDays / 365);

	if (diffSeconds < 60) {
		return 'just now';
	} else if (diffMinutes < 60) {
		return `${diffMinutes} ${diffMinutes === 1 ? 'minute' : 'minutes'} ago`;
	} else if (diffHours < 24) {
		return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
	} else if (diffDays < 7) {
		return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;
	} else if (diffWeeks < 4) {
		return `${diffWeeks} ${diffWeeks === 1 ? 'week' : 'weeks'} ago`;
	} else if (diffMonths < 12) {
		return `${diffMonths} ${diffMonths === 1 ? 'month' : 'months'} ago`;
	} else {
		return `${diffYears} ${diffYears === 1 ? 'year' : 'years'} ago`;
	}
}

/**
 * Format a date string to absolute date (e.g., "Jan 15, 2024")
 * @param dateStr - ISO 8601 date string
 * @returns Formatted date string
 */
export function formatAbsoluteDate(dateStr: string): string {
	const date = new Date(dateStr);
	return date.toLocaleDateString('en-US', {
		month: 'short',
		day: 'numeric',
		year: 'numeric'
	});
}
