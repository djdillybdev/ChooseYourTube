interface FrameSize {
	width: number;
	height: number;
}

/**
 * Fit a 16:9 frame inside a container while respecting a max width.
 */
export function fit16x9(containerWidth: number, containerHeight: number, maxWidth: number): FrameSize {
	if (containerWidth <= 0 || containerHeight <= 0 || maxWidth <= 0) {
		return { width: 0, height: 0 };
	}

	const cappedWidth = Math.min(containerWidth, maxWidth);
	let width = cappedWidth;
	let height = (width * 9) / 16;

	if (height > containerHeight) {
		height = containerHeight;
		width = (height * 16) / 9;
	}

	return {
		width: Math.floor(width),
		height: Math.floor(height)
	};
}
