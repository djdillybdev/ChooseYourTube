/**
 * Format video duration in seconds to readable format
 * @param seconds - Duration in seconds
 * @returns Formatted duration (e.g., "1:23", "12:34", "1:23:45")
 */
export function formatDuration(seconds: number | null | undefined): string {
	if (!seconds || seconds < 0) return '0:00';

	const h = Math.floor(seconds / 3600);
	const m = Math.floor((seconds % 3600) / 60);
	const s = Math.floor(seconds % 60);

	// Pad single digits with leading zero
	const padZero = (num: number) => num.toString().padStart(2, '0');

	if (h > 0) {
		// Format: H:MM:SS
		return `${h}:${padZero(m)}:${padZero(s)}`;
	} else {
		// Format: M:SS
		return `${m}:${padZero(s)}`;
	}
}
