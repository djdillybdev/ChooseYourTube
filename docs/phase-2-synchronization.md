# Phase 2 synchronization operations

ChooseYourTube records every background synchronization in `sync_runs`. Manual channel
and playlist refresh endpoints return the durable run with HTTP 202; clients can poll
`GET /sync-runs/{id}` or review recent activity under **Settings → Sync Activity**.

The worker uses the sync-run UUID as its arq job ID. A PostgreSQL partial unique index
prevents concurrent queued/running runs for the same owner, channel, and kind. Transient
failures retry after approximately 1, 5, and 30 minutes, for four total attempts. Safe
terminal failures can be retried through `POST /sync-runs/{id}/retry`.

Channel refreshes fetch RSS asynchronously with conditional requests, bounded response
size, and explicit timeouts before using the YouTube Data API. All runtime YouTube API
calls pass through daily quota accounting. `GET /sync-runs/quota` exposes authenticated,
aggregate usage without credentials or upstream response bodies.

The hourly scheduler runs in UTC, scans all channels in batches, and distributes jobs
across the next 50 minutes. A Redis lock and active-run uniqueness prevent overlapping
scheduler invocations. Worker availability remains visible through `/health/ready`.
