#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
demo_url="${PORTFOLIO_BASE_URL:-https://chooseyourtube-demo-tawny.vercel.app}"
artifact_dir="$repo_dir/.portfolio-artifacts"
source_video="$artifact_dir/chooseyourtube-demo-v1.0.0.webm"
output_video="$artifact_dir/chooseyourtube-demo-v1.0.0.mp4"

if ! command -v ffmpeg >/dev/null 2>&1; then
	echo "ffmpeg is required to produce the captioned release MP4." >&2
	exit 1
fi

cd "$repo_dir/frontend"
CAPTURE_PORTFOLIO_VIDEO=1 PORTFOLIO_BASE_URL="$demo_url" \
	pnpm exec playwright test portfolio-screenshots.test.ts --grep "record portfolio walkthrough"

mkdir -p "$artifact_dir"
ffmpeg -y -i "$source_video" -t 119 -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p \
	-movflags +faststart -an "$output_video"

echo "Created $output_video"
