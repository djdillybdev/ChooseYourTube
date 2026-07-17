# ChooseYourTube Portfolio-Ready v1.0 Implementation Plan

> Historical implementation record. For current project documentation, start at
> [`docs/README.md`](README.md).

## 1. Purpose and release outcome

ChooseYourTube is a self-hostable YouTube feed reader that lets users follow selected channels, organize them, find videos, and watch without YouTube's recommendation-driven interface. The portfolio release must be understandable and demonstrable to a recruiter in a few minutes while remaining a credible, usable self-hosted application.

The v1.0 release has two supported runtime configurations built from the same `main` branch:

1. **Hosted demo:** SvelteKit and FastAPI run on Vercel and use a hosted Neon PostgreSQL database. A recruiter enters a seeded shared account using a one-click demo button. Quota-sensitive operations are disabled, and mutable demo state is reset daily.
2. **Full self-hosted application:** Docker Compose runs SvelteKit, FastAPI, PostgreSQL, Redis, Alembic migrations, and arq workers. It supports user accounts, hourly refreshes, Google OAuth and CSV subscription imports, and a user-supplied YouTube API key.

The release is complete when a recruiter can understand the project from GitHub, open a working demo without credentials, exercise its principal workflows, and see clear evidence of production-oriented engineering. A self-hoster must also be able to start the complete application using the documented Docker workflow.

Do not create a permanent demo branch. Demo and full deployments must share models, services, migrations, frontend components, and tests. Runtime flags and deployment-specific entrypoints should contain the small amount of behavior that differs between the two modes. This prevents fixes and schema changes from drifting between branches.

## 2. Current repository baseline

The repository is already a monorepo with:

- A Svelte 5/SvelteKit TypeScript frontend using Tailwind CSS and DaisyUI.
- A FastAPI backend using async SQLAlchemy, Alembic, PostgreSQL, and FastAPI Users.
- Redis and arq for background tasks and hourly scheduling.
- YouTube Data API and RSS integrations.
- Per-user ownership through `owner_id` on core entities.
- Channels, videos, nested folders, tags, manual playlists, channel-synced playlists, a queue/player, watched and favorite state, full-text video search, filtering, sorting, and pagination.
- Rotating refresh-token sessions exposed to the browser through SvelteKit server-side auth routes and HTTP-only cookies.
- Backend tests organized by router, service, CRUD, worker, unit, and property-based scopes.
- Frontend unit, component, and Playwright test infrastructure.
- A root Docker Compose stack containing frontend, backend, worker, PostgreSQL, Redis, and a one-shot migration service.

The main gaps are:

- There is no subscription import workflow.
- Watch Later is not an explicit first-class system playlist.
- Tag/category CRUD exists in the backend but is not a complete user-facing workflow.
- Background jobs do not have durable, user-visible status or structured failure recovery.
- The scheduler currently requests only the default page of channels, which can omit channels after the first page.
- Manual video refresh is synchronous while playlist refresh is queued, creating inconsistent behavior.
- Worker results are discarded and errors are primarily logs or raw messages.
- RSS fetching is blocking and lacks explicit timeout/conditional-request behavior.
- Health checks do not fully distinguish liveness, dependency readiness, and worker availability.
- GitHub Actions are absent, and the single Playwright test only verifies an unauthenticated redirect.
- The root README does not yet explain the full current architecture or provide recruiter-oriented screenshots, decisions, trade-offs, and demo media.
- The frontend README is still framework-generated boilerplate, and some package/API metadata remains placeholder text.
- The current SvelteKit adapter targets Node only; Vercel requires an adapter/deployment configuration while Docker must continue using the Node adapter.

Before feature work, run and record the full baseline. Dependency installation and generated caches are allowed, but the baseline task must not silently rewrite source files.

```bash
# Backend
cd backend
uv sync
uv run ruff check app tests
uv run mypy app
uv run pytest

# Frontend
cd frontend
pnpm install --frozen-lockfile
pnpm run check
pnpm run lint
pnpm run test:coverage
pnpm run test:e2e

# Root stack
docker compose --env-file .env.example config --quiet
docker compose --env-file .env up -d --build
docker compose --env-file .env ps
```

Record failing checks as issues or checklist entries, then make the baseline green before introducing schema and API changes. Preserve unrelated user changes in a dirty worktree.

## 3. Delivery order and dependencies

Implement the release in the following order. Each phase should land as one or more focused commits with its tests and documentation included.

1. Stabilize the baseline and configuration.
2. Add durable synchronization state and reliable background execution.
3. Add Watch Later and complete categories.
4. Add the shared subscription-import pipeline, followed by CSV and OAuth sources.
5. Polish authentication, demo behavior, error handling, responsive UX, and accessibility.
6. Expand automated testing and add GitHub Actions.
7. Produce Docker release artifacts and the Vercel demo.
8. Complete portfolio documentation, screenshots, video, and the `v1.0.0` release.

Synchronization is deliberately before import because imports need the same durable job state, idempotency, progress reporting, and failure model. The demo deployment comes after core behavior and CI so it deploys the release candidate rather than becoming a parallel development target.

## 4. Phase 1: baseline, configuration, and operational foundations

### 4.1 Clean up project identity

- Replace the backend package placeholder description and the API root `Hello World` response with ChooseYourTube metadata and links to health/docs endpoints.
- Replace the generated frontend README with concise frontend-specific development instructions, while keeping the root README as the primary project entrypoint.
- Ensure package versions, Python/Node requirements, license references, and application names agree across manifests and docs.
- Generate frontend API types from the backend OpenAPI schema or add an explicit documented command that verifies the checked-in types/schema are current. CI must fail on schema drift.

### 4.2 Introduce explicit runtime modes

Add typed settings with the following behavior:

| Setting                      | Full mode default       | Demo mode default | Purpose                                                  |
| ---------------------------- | ----------------------- | ----------------- | -------------------------------------------------------- |
| `APP_MODE`                   | `full`                  | `demo`            | Selects supported runtime behavior.                      |
| `REGISTRATION_ENABLED`       | `true`                  | `false`           | Enables public account registration.                     |
| `BACKGROUND_JOBS_ENABLED`    | `true`                  | `false`           | Enables Redis/arq enqueue operations.                    |
| `YOUTUBE_OAUTH_ENABLED`      | When configured         | `false`           | Enables Google subscription OAuth.                       |
| `DEMO_LOGIN_ENABLED`         | `false`                 | `true`            | Enables one-click demo sessions.                         |
| `YOUTUBE_DAILY_QUOTA_BUDGET` | Configurable safe value | Unused            | Stops optional full-mode work before quota is exhausted. |
| `DEMO_USER_EMAIL`            | Unset                   | Required          | Identifies the seeded shared demo user.                  |
| `DEMO_MAINTENANCE_SECRET`    | Unset                   | Required          | Protects daily demo maintenance.                         |

Make `REDIS_URL` required only when background jobs are enabled. Google OAuth client settings are optional, but attempting to enable OAuth without them must fail startup validation. A YouTube API key remains required for full live synchronization. Demo mode never requires or uses a key: its maintenance path creates videos directly from public channel RSS metadata and reports per-feed failures without deleting the last durable data.

Outside local development, reject the placeholder `AUTH_SECRET`, wildcard CORS, insecure OAuth transport, malformed origins, and secrets shorter than the documented minimum. Remove the OAuth client behavior that sets `OAUTHLIB_INSECURE_TRANSPORT` globally; allow insecure redirect URIs only under an explicit local-development flag.

### 4.3 Health, logging, and error contracts

Replace or supplement the existing health routes with:

- `GET /health/live`: always cheap; returns process/application identity and `200` if the process can serve requests.
- `GET /health/ready`: checks database connectivity and migration compatibility. In full mode it also checks Redis and a recent worker heartbeat. In demo mode it explicitly reports Redis/worker as not required. Return `503` when a required dependency is unavailable.

Do not expose raw connection strings, SQL, stack traces, OAuth tokens, or Google response bodies through health or user-facing errors.

Use structured application logging. Every request should have a request/correlation ID. Sync-related logs must include `sync_run_id`, task kind, owner ID, channel/import ID when relevant, attempt, duration, and outcome. User-visible errors should use a stable code plus safe message; detailed exception information remains in logs.

Define a shared API error body:

```json
{
  "code": "YOUTUBE_QUOTA_EXHAUSTED",
  "message": "YouTube refresh is temporarily unavailable because the daily quota was reached.",
  "request_id": "...",
  "retryable": false
}
```

The frontend API client must extract this body, map known codes to actionable UI, and fall back to a generic request-ID-bearing message.

## 5. Phase 2: reliable and visible synchronization

### 5.1 Durable data model

Add an Alembic migration and SQLAlchemy/Pydantic models for `sync_runs`.

Required fields:

- UUID `id`.
- `owner_id` with deletion behavior consistent with other owned data.
- `kind`: `initial_channel_sync`, `channel_refresh`, `playlist_sync`, `subscription_import`, or `demo_maintenance`.
- `status`: `queued`, `running`, `succeeded`, `partial`, or `failed`.
- Optional `channel_id` and `subscription_import_id`.
- `attempt_count` and `max_attempts`.
- `items_discovered`, `items_created`, `items_updated`, `items_skipped`, and `items_failed`.
- Safe `error_code` and `error_message`; never persist tokens or sensitive upstream payloads.
- `queued_at`, `started_at`, `finished_at`, and `next_retry_at`.
- `created_at`/`updated_at` if not covered by the above lifecycle timestamps.

Add indexes for owner plus recency, status, channel, and import. Enforce at most one active (`queued` or `running`) run for the same owner/channel/kind through a safe application-level enqueue transaction or a PostgreSQL partial unique index. Use the sync-run UUID as the arq `_job_id` so duplicate delivery/enqueue cannot create parallel work.

Add a small worker-heartbeat record or Redis key containing worker identity and last-seen time. Refresh it periodically from arq startup/health work. Full-mode readiness should consider a heartbeat stale after a documented interval longer than the heartbeat frequency.

### 5.2 API changes

Add:

- `GET /sync-runs?status=&kind=&channel_id=&limit=&offset=` returning an owner-scoped paginated response.
- `GET /sync-runs/{sync_run_id}` returning only the current owner's run.
- A compact `latest_sync` summary on `ChannelOut`, or a separately fetched map if query analysis shows that embedding it creates an N+1 problem.

Change refresh commands to consistent asynchronous contracts in full mode:

- `POST /channels/{channel_id}/refresh` returns `202` and `SyncRunOut`.
- `POST /channels/{channel_id}/playlists/refresh` returns `202` and `SyncRunOut`.

If an equivalent active run exists, return that existing run instead of enqueueing another. In demo mode, recruiter-triggered external refresh returns `403` with `FEATURE_DISABLED_IN_DEMO`; the UI explains that the displayed data is refreshed by daily maintenance.

### 5.3 Worker lifecycle and retry policy

Refactor every task through a common runner that:

1. Atomically claims a queued run and sets it to running.
2. Records the attempt and start time.
3. Executes idempotent service logic.
4. Updates counters as batches commit.
5. Sets a terminal status and finish time.
6. On a retryable exception, records the failure and schedules the next attempt.

Retry transient timeouts, connection failures, HTTP 429, and upstream 5xx errors after approximately 1 minute, 5 minutes, and 30 minutes, with no more than three attempts. Do not immediately retry invalid credentials, invalid channel IDs, authorization denial, malformed configuration, or daily quota exhaustion. Quota-exhausted work may become eligible after the next UTC quota window through a new run rather than an unbounded worker retry.

All database writes must remain idempotent. Video IDs, channel IDs, source playlist IDs, and ordered playlist membership must not duplicate when jobs are delivered twice. Partial batches should be committed deliberately so the run can report useful progress, and subsequent attempts must skip already-completed work.

### 5.4 RSS-first refresh and quota accounting

- Replace direct blocking `feedparser.parse(url)` calls with an async HTTP request using explicit connect/read timeouts and bounded response size.
- Store RSS `ETag` and `Last-Modified` values per channel, send conditional requests, and treat `304` as a successful no-change refresh.
- Parse downloaded bytes off the event loop if parsing is not demonstrably cheap.
- Validate feed shape defensively; a missing `yt_videoid`, link, or entries collection must produce a classified error rather than an attribute exception.
- Continue using RSS to detect likely changes before spending Data API quota.
- Batch `videos.list` and `channels.list` calls up to their supported batch sizes.

The Vercel demo is stricter than the full synchronization path: it builds recent video records directly
from RSS and must never instantiate the YouTube Data API client or fall back to quota-metered endpoints.

Add daily external API usage accounting with date, operation, estimated units, call count, and outcome. Increment it through one instrumented YouTube client wrapper so service code cannot bypass accounting. Stop optional API work when `YOUTUBE_DAILY_QUOTA_BUDGET` is reached. Expose only aggregate, non-secret quota status to authenticated users.

### 5.5 Scheduler correctness

- Paginate or stream through every saved channel; never rely on the current `get_all_channels` default limit.
- Schedule in UTC and document the intended hourly cadence.
- Stagger jobs to smooth quota and load.
- Use active-run deduplication/distributed locking to avoid overlapping cron invocations.
- Ensure one user's invalid channel cannot stop scheduling for other users.

### 5.6 Frontend status experience

- Show latest successful refresh, current state, and safe failure message on channel pages/cards.
- After a manual refresh, poll the returned sync-run endpoint with bounded backoff until terminal or until the page is left.
- Announce queued, completed, and failed states through a polite live region.
- Provide Retry only for terminal failures that are safe to retry.
- Preserve the last successfully loaded videos when a refresh fails.
- Add a recent activity/status view, either in Settings or a compact global panel, so background failures are visible without visiting each channel.

## 6. Phase 3: Watch Later and complete organization

### 6.1 Watch Later model and API

Add a nullable `system_key` to playlists and a unique constraint on `(owner_id, system_key)` where the key is non-null. Use `watch_later` as the reserved value. Keep existing `source_type` semantics for manual and YouTube/channel-synced playlists; do not overload a channel-synced playlist as Watch Later.

Create Watch Later during normal user initialization and also provide an idempotent `ensure_watch_later(owner_id)` path so existing users receive it without a brittle data backfill. The playlist name may be localized or changed later, so business logic must identify it by `system_key`, not name.

Add:

- `GET /playlists/watch-later` returning `PlaylistDetailOut`.
- `PUT /playlists/watch-later/videos/{video_id}` adding the video idempotently.
- `DELETE /playlists/watch-later/videos/{video_id}` removing it idempotently.

`PlaylistOut` and `PlaylistDetailOut` gain `system_key: string | null`. User-created playlist requests must not accept arbitrary system keys. Watch Later cannot be renamed or deleted through general playlist endpoints.

### 6.2 Watch Later UI

- Add Watch Later as a prominent sidebar destination.
- Add an accessible one-click save/remove button to each video card and the player.
- Use optimistic UI with rollback and a visible error if persistence fails.
- Add an empty state explaining how to save a video.
- Reuse ordered playlist playback and current-position behavior.
- Make the general Save to Playlist modal clearly distinguish Watch Later from custom playlists without duplicating membership requests per playlist.

### 6.3 Categories and tags

Define the user-facing organization model consistently:

- **Folders** categorize channels hierarchically.
- **Tags** categorize both channels and individual videos across folders.
- **Playlists** represent explicit ordered collections of videos.

Turn `/settings` into a real settings/category area rather than redirecting to `/inbox`.

- Add tag list, create, rename, and delete workflows.
- Show usage counts where inexpensive; otherwise warn generically that deletion removes the tag association from channels/videos.
- Add tag assignment to the channel edit modal.
- Add tag assignment to the video save/edit workflow.
- Validate tag names consistently on frontend and backend, including trimming, case normalization, length, and per-owner uniqueness.
- Make folder and tag filters use URL query parameters and reset pagination when changed.

## 7. Phase 4: subscription importing

### 7.1 Shared import data model

Add `subscription_imports` and `subscription_import_candidates`.

The import record contains:

- UUID and owner.
- `source`: `youtube_oauth` or `youtube_takeout_csv`.
- `status`: `collecting`, `ready`, `queued`, `running`, `succeeded`, `partial`, or `failed`.
- Candidate/new/existing/invalid/selected/imported/failed counts.
- Optional destination folder ID and tag IDs chosen at commit.
- Safe error code/message and lifecycle timestamps.

Each candidate contains:

- Import ID and owner.
- YouTube channel ID when valid.
- Channel title and URL when provided.
- `state`: `new`, `existing`, `invalid`, `selected`, `imported`, or `failed`.
- Source row/index for CSV error reporting.
- Safe validation/failure message.

Index by import and state. Enforce owner scoping in every query. Imports are additive: they never remove channels that are absent from the imported source.

### 7.2 Public import interfaces

Add:

- `POST /imports/subscriptions/csv` as multipart upload; returns an import preview.
- `GET /imports/youtube/oauth/start`; returns an authorization URL or redirects through a dedicated frontend route.
- `GET /imports/youtube/oauth/callback`; validates one-use state, exchanges the code, collects subscription candidates, and redirects to the frontend import review page.
- `GET /imports/{import_id}`; returns import metadata and paginated candidates.
- `PATCH /imports/{import_id}/candidates`; updates selected candidate IDs if selection is persisted server-side.
- `POST /imports/{import_id}/commit`; accepts selected IDs plus optional folder/tag assignment and returns a `202` sync run.

The frontend backend-proxy allowlist must be expanded deliberately for these routes. File upload proxying must preserve multipart content rather than treating every non-GET body as plain text.

### 7.3 Google OAuth source

- Use Google's web authorization-code flow with a cryptographically random, hashed, one-use state record tied to the signed-in ChooseYourTube user and expiring after ten minutes.
- Request the minimum read-only YouTube scope needed for `subscriptions.list(mine=true)`.
- Fetch every page with `maxResults=50` and normalize `snippet.resourceId.channelId`.
- Perform subscription discovery during/after the callback, store only normalized candidates, and discard Google access/refresh tokens when discovery finishes.
- Do not persist Google tokens because v1.0 imports once rather than maintaining an ongoing Google-account connection.
- Treat denied consent, expired state, replayed state, missing YouTube channel, and Google API errors as explicit recoverable UI states.
- The old installed-app console OAuth flow must not be used by the web application.

After candidates are stored, the commit worker uses the application's API key to batch channel metadata lookup and reuse normal idempotent channel creation/synchronization services. This avoids persisting a user's OAuth credentials across background jobs.

### 7.4 Google Takeout CSV source

- Limit uploads to 2 MB and 5,000 data rows.
- Accept the known Takeout channel ID, channel URL, and channel title columns while tolerating reasonable header capitalization/order changes.
- Normalize channel IDs from direct IDs and supported channel URLs.
- Reject formula-style spreadsheet payloads from being reflected/exported unsafely.
- Deduplicate candidates within the file and classify channels already followed by the current user.
- Preserve valid rows when other rows are invalid and present row-level errors in the preview.
- Do not store the original uploaded file after parsing.

### 7.5 Import UI

Add a guided import page accessible from Add Channel and Settings:

1. Choose Google OAuth or Takeout CSV.
2. Collect/parse subscriptions.
3. Review counts and searchable candidates grouped into new, existing, and invalid.
4. Select new channels and optionally choose a folder and tags.
5. Commit and show durable progress through the associated sync run.
6. Present imported/skipped/failed totals and retry only failed candidates.

Disable OAuth and CSV imports for the shared Vercel demo account with an explanation and a visible sample import preview/status in the seed data. The complete functionality remains available in Docker full mode.

## 8. Phase 5: accounts, demo safeguards, UX, and accessibility

### 8.1 Full-mode accounts

- Retain registration, password login, logout, current-user lookup, short-lived access tokens, and rotating refresh sessions.
- Ensure login/register errors show stable messages instead of raw enum codes.
- Verify cookies are HTTP-only, secure in HTTPS deployments, use an appropriate SameSite value, and are cleared consistently on invalid refresh/logout.
- Either provide a configured email delivery path for reset/verification or hide/disable those incomplete flows in v1.0. Do not advertise routes users cannot complete.
- Ensure deletion/export expectations are documented. All owned data must cascade or be deleted transactionally when an account is removed.

### 8.2 Hosted demo account

Add `POST /auth/demo`, available only when `APP_MODE=demo` and `DEMO_LOGIN_ENABLED=true`.

- It creates the same normal access/refresh session shape as password login for the configured seeded account.
- It does not expose a password or grant superuser privileges.
- The login page shows a primary **Try the demo** button and keeps normal login/registration UI hidden in demo mode.
- A persistent banner states that this is a shared demo and changes reset daily.
- Disable registration, imports, channel creation/deletion, manual YouTube refresh, account mutation, and other quota/destructive operations.
- Allow safe interactions needed to demonstrate skills: searching/filtering, watched state, favorites, Watch Later, custom demo playlists, categories, and playback.
- Enforce restrictions in backend authorization/service logic, not only by hiding buttons.

### 8.3 General UX completion

- Add loading skeletons, empty states, retry states, partial-result warnings, session-expired handling, and destructive confirmations to every primary workflow.
- Preserve loaded data when a non-destructive background request fails.
- Ensure browser Back/Forward works for search, filters, pagination, channel tabs, and import steps where appropriate.
- Replace `window.confirm` with an accessible confirmation dialog for destructive actions.
- Give every page a meaningful title and description.
- Complete phone, tablet, and desktop layouts. At minimum, verify 375 px, 768 px, and 1280 px widths.
- Make the sidebar usable as a keyboard-accessible mobile drawer and prevent focus from reaching obscured content.
- Ensure the player remains usable in constrained heights and that error-skipping behavior is visible rather than silent.

### 8.4 WCAG 2.2 AA target

- Add a skip-to-content link and stable `main`, `nav`, `header`, and complementary landmarks.
- Give all controls accessible names; use actual `<label>` elements for selects/date inputs rather than nearby visual text.
- Use visible focus indicators and logical DOM/tab order.
- Make custom filters, menus, disclosure widgets, and folder trees keyboard operable.
- Trap focus inside dialogs, support Escape, restore focus to the trigger, and prevent duplicate close controls from confusing screen readers.
- Add `aria-live` regions for asynchronous save, refresh, import, and error feedback.
- Use meaningful image alternatives; decorative SVGs should be hidden from assistive technology.
- Meet text/non-text contrast requirements in all used DaisyUI states.
- Support 200% zoom and reduced-motion preferences.
- Verify keyboard-only use and screen-reader reading order manually in addition to automated checks.

## 9. Phase 6: tests and GitHub Actions

### 9.1 Backend coverage

Add unit/service/router/worker tests for:

- Runtime-mode validation and secure production defaults.
- Liveness/readiness with optional and required dependencies.
- Sync-run lifecycle, owner isolation, active-run deduplication, counters, and terminal states.
- Retry classification for timeout, 429, 5xx, invalid credentials, and quota exhaustion.
- Duplicate job delivery and idempotent writes.
- RSS no-change, conditional request, malformed feed, timeout, and new-video paths.
- Scheduler pagination beyond 50 channels and isolation of per-channel failures.
- Watch Later lazy creation, uniqueness, idempotent add/remove, and immutability.
- Tag/category ownership and deletion behavior.
- OAuth state expiration/replay/denial and token-discard behavior.
- CSV variations, duplicates, invalid rows, size/row limits, and cross-user access.
- Import preview, partial commit, retry, and destination folder/tag validation.
- Demo endpoint availability by mode and backend enforcement of disabled operations.
- Alembic upgrade from an empty database and migration-head integrity.

Require at least 80% backend line/branch coverage. Critical auth, ownership, import, quota, and worker code needs direct tests even if aggregate coverage passes.

### 9.2 Frontend coverage

Maintain at least the current 70% line/branch/function/statement thresholds and expand the configured coverage include list to new critical code.

Test:

- Stable API error parsing and refresh-token behavior.
- One-click demo login and mode-sensitive navigation.
- Watch Later optimistic updates and rollback.
- Tag management and assignment.
- Import choice, preview, selection, commit, progress, and partial failures.
- Refresh polling and retry states.
- Accessible modal focus/keyboard behavior.
- Mobile sidebar and filter interactions.

### 9.3 End-to-end coverage

Run Playwright against a deterministic seeded stack. Cover:

1. Unauthenticated redirect and full-mode register/login/logout.
2. One-click demo entry.
3. Inbox search and combined watched/channel/tag/date/short filters.
4. Watched/unwatched and favorite transitions.
5. Watch Later add, remove, and playback.
6. Folder and tag organization.
7. CSV import preview with valid, duplicate, existing, and invalid rows.
8. Import progress and partial failure.
9. Manual refresh status and retry using mocked YouTube responses.
10. Cross-user resource isolation.
11. Expired session refresh and forced reauthentication.

Use `@axe-core/playwright` on login, inbox, channel, playlist, player, import, and settings pages. CI must have no serious or critical axe violations. Keep a manual WCAG checklist because automated tools do not prove conformance.

### 9.4 CI workflows

Add pull-request workflows with parallel jobs:

- **Backend quality:** install from `uv.lock`, Ruff, mypy, pytest with coverage, PostgreSQL/Redis services where required, and migration integrity.
- **Frontend quality:** frozen pnpm install, formatting check, ESLint, Svelte check, Vitest, and coverage.
- **E2E:** build/start the seeded stack and run Playwright plus axe.
- **Containers:** build production frontend/backend images and run a Compose smoke test covering migration completion, readiness, login, and an authenticated API call.
- **Schema drift:** regenerate/compare OpenAPI and frontend types without committing generated changes.

Cache package downloads without caching secrets or mutable test databases. Cancel superseded runs on the same branch.

Add a tagged-release workflow that builds versioned multi-architecture images, publishes them to GitHub Container Registry, produces checksums/provenance where practical, and creates GitHub release notes. Add a protected, manually dispatchable production-migration workflow using the Neon direct database URL; it must run `alembic current`, upgrade to head, and verify the schema before deployment promotion.

## 10. Phase 7: deployment and release packaging

### 10.1 Vercel architecture

Configure two Vercel projects from the same repository:

- **Frontend project:** root directory `frontend/`, SvelteKit with `adapter-vercel`.
- **Backend project:** root directory `backend/`, FastAPI exported through a Vercel-supported entrypoint or project script.

Select the SvelteKit adapter based on the build target so Docker continues to produce an adapter-node server. Keep the existing SvelteKit server-side backend proxy: browser auth cookies remain same-origin, while the server uses `API_BASE_URL` to reach the backend project.

Use separate preview and production environment variables. CORS should allow only the expected frontend origins, though normal browser API traffic should pass through the frontend proxy. Ensure OAuth redirect URIs exactly match production/local callback URLs.

Use Neon pooled PostgreSQL connections for request traffic and the direct connection string for Alembic. Configure connection pool behavior for ephemeral functions and avoid assuming process-global connections survive. Do not run migrations automatically during every Vercel build or cold start.

FastAPI runs as a Vercel Function, not a persistent worker. Vercel Hobby cron supports only daily execution and may invoke it within the configured hour. Therefore the demo intentionally does not run Redis/arq or promise hourly refreshes. The full Docker deployment remains the reference background-worker architecture.

### 10.2 Demo seed and maintenance

Create a deterministic, versioned seed definition and idempotent seeding service/script. It should create:

- One non-superuser demo account.
- A small curated set of public channels covering varied content.
- Enough videos to demonstrate search, dates, Shorts filtering, pagination, and player queues.
- Nested folders and several tags.
- A deliberate mix of watched, unwatched, and favorited videos.
- Watch Later and custom playlists with ordered content/current position.
- At least one representative successful and one historical failed/recovered sync record.
- A representative completed import record for explaining the disabled demo import UI.

Do not commit secrets or downloaded media. Remote YouTube thumbnails/player embeds may be referenced in normal application data; seed logic must tolerate missing/changed thumbnails.

Add a secret-protected daily maintenance endpoint invoked by Vercel cron. It must:

1. Authenticate the cron secret and reject normal users.
2. Create a `demo_maintenance` sync run.
3. Attempt a bounded RSS-only refresh of the curated channels without constructing or calling the YouTube Data API client.
4. Reset watched/favorite/category/playlist state to the seed definition transactionally.
5. Preserve the last good videos if YouTube is unavailable.
6. Clean expired auth refresh sessions.
7. Finish with visible success/partial/failure counters and structured logs.

The demo must remain usable if the daily cron, YouTube, or Redis is unavailable. Read paths use the last durable PostgreSQL dataset.

### 10.3 Full Docker distribution

Keep the existing services: frontend, backend, worker, PostgreSQL, Redis, and one-shot migrate.

- Add exact health dependencies and readiness semantics.
- Add graceful shutdown and sensible restart policies.
- Document persistent volumes and expected resource use.
- Ensure API/worker startup does not race migrations.
- Add `make quickstart`, `make test`, `make health`, `make backup`, and `make restore` targets.
- Provide a development Compose flow using local builds and a release Compose override using pinned GHCR `v1.x` images.
- Document full reset separately and clearly mark it destructive.
- Test upgrades from the previous schema as well as fresh installs.

The quick start should require only Git, Docker/Compose, a generated auth secret, and a user-provided YouTube API key. Google OAuth client credentials are optional because Takeout CSV import remains supported.

### 10.4 Release operations

- Deploy migrations before the Vercel backend version that depends on them.
- Run production smoke tests for demo login, inbox load, search, Watch Later, and readiness.
- Verify logs contain request/sync IDs but no secrets.
- Exercise rollback of the frontend/backend deployment while maintaining schema compatibility.
- Document database backup/export and demo reseeding.
- Monitor Vercel/Neon usage and YouTube quota during the initial release period.

## 11. Phase 8: recruiter-facing documentation and media

### 11.1 Root README structure

Rewrite the root README in this order:

1. Project name, concise value proposition, and hero screenshot.
2. **Live Demo** and **90–120 second Video** links above the fold.
3. CI, release, license, and accessibility status badges.
4. The problem being solved and intended audience.
5. Feature highlights, explicitly including accounts, import, organization, search/filtering, Watch Later, background synchronization, and recovery.
6. Four screenshots: inbox/filtering, folders/tags, Watch Later/player, and import/sync status.
7. Mermaid architecture diagram showing browser, SvelteKit proxy, FastAPI, PostgreSQL, Redis/arq, YouTube Data API, and RSS. Mark Vercel demo and Docker-only components clearly.
8. Five-minute Docker quick start.
9. Full configuration table with required/optional/mode-specific variables.
10. Testing and development commands.
11. Engineering decisions and known trade-offs.
12. Security/privacy/data-ownership notes.
13. Deployment and upgrade links.
14. AI-assistance disclosure phrased transparently around reviewed contributions, design ownership, and verification rather than diminishing the project.

### 11.2 Engineering decisions to explain

Document these explicitly in the README or linked architecture decision records:

- RSS-first change detection reduces quota use in full mode; the Data API fills metadata gaps there, while the Vercel demo remains RSS-only.
- PostgreSQL is the durable application cache and source of truth.
- Content is currently duplicated per owner, which favors isolation and straightforward deletion but costs storage and repeated refresh work.
- Google OAuth tokens are discarded after subscription discovery to minimize sensitive data retention; CSV is the privacy-friendly fallback.
- Redis/arq handles the full deployment's asynchronous workload, while durable PostgreSQL sync records make execution observable and recoverable.
- Idempotent job IDs/upserts make retries safe.
- The Vercel demo trades hourly workers and write-heavy external integrations for a safe free-tier recruiter experience.
- The hosted and Docker paths share code and migrations rather than diverging into branches.
- Search uses PostgreSQL full-text search, accepting database-specific behavior for stronger relevance/performance.

### 11.3 Additional portfolio documents

Add:

- `docs/architecture.md`: component boundaries, request/data flow, worker flow, tenancy, and both deployment topologies.
- `docs/deployment.md`: Docker and Vercel/Neon deployment, migration, environment, backup, restore, and rollback.
- `docs/demo-script.md`: a two-minute recruiter walkthrough and a longer interview walkthrough.
- `docs/engineering-decisions.md` or focused ADRs for quota strategy, data ownership, OAuth token handling, durable jobs, and demo/full divergence.
- `docs/accessibility.md`: target, automated checks, manual checklist, known limitations, and audit date.
- `SECURITY.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` at repository root.

The interview guide should map product actions to engineering discussions: API quotas, caching, asynchronous workers, data ownership, synchronization, deployment, authentication, idempotency, and failure recovery.

### 11.4 Screenshots, video, and GitHub presentation

- Capture screenshots at a consistent desktop size using deterministic demo data. Store optimized images under `docs/images/` with useful filenames and alt text in Markdown.
- Record a captioned 1080p video lasting 90–120 seconds:
  1. Enter through one-click demo.
  2. Explain the distraction-free subscription inbox.
  3. Show folders/tags, search, and combined filters.
  4. Mark watched and add a video to Watch Later.
  5. Start playlist/player playback.
  6. Show subscription-import preview and sync/error visibility.
  7. End on the architecture diagram and CI/test evidence.
- Host the video somewhere stable and link an image thumbnail from the README. Include captions/transcript.
- Set the GitHub repository description, website/demo URL, topics, and social preview image.
- Create `v1.0.0` with a curated changelog, installation notes, demo link, video link, image references, and known trade-offs.

## 12. Public interface and schema change summary

The implementer should expect these public changes:

- `ChannelOut` gains a latest-sync summary or the frontend gains an equivalent batched sync lookup.
- Playlist output gains `system_key`; create/update input must not allow clients to manufacture system playlists.
- New `SyncRunOut`, `SubscriptionImportOut`, and `SubscriptionImportCandidateOut` schemas and their paginated forms.
- Refresh endpoints change from synchronous/channel-shaped responses to `202 SyncRunOut`.
- New sync-run, Watch Later, subscription-import, demo-login, liveness/readiness, and internal demo-maintenance routes.
- A stable structured error response replaces assumptions about arbitrary FastAPI `detail` values.
- Frontend proxy allowlists and body forwarding expand for imports and multipart files.
- New migrations add sync runs, API usage accounting, RSS conditional-request fields, playlist system keys, imports/candidates, and any worker-heartbeat persistence chosen over Redis.

Regenerate OpenAPI and frontend TypeScript types after backend interface changes. Note breaking changes in the changelog; compatibility with unreleased internal API consumers is not required, but the frontend and backend must always be released together.

## 13. Definition of done

The release must meet all of the following:

### Recruiter experience

- The GitHub landing page explains the value in under one screen and links directly to the demo/video.
- The hosted URL loads over HTTPS and offers one-click demo entry with no credentials.
- A recruiter can search/filter, organize content, change watched state, use Watch Later, and play videos.
- Demo restrictions and daily reset behavior are clearly explained, not presented as unexplained errors.
- Seed data remains usable after YouTube or cron failure.

### Full product

- A new user can install with documented Docker commands and register/login.
- OAuth and Takeout CSV imports handle duplicates, invalid rows, and partial failure.
- Folders, tags, watched state, Watch Later, manual playlists, and synced playlists are owner-isolated.
- Hourly scheduling reaches every channel and avoids duplicate active work.
- Every background operation has durable progress, a terminal outcome, safe errors, and a retry policy.
- Backup, restore, upgrade, reset, and troubleshooting procedures are documented and tested.

### Quality and accessibility

- All required GitHub checks pass.
- Backend coverage is at least 80%; frontend coverage is at least 70%.
- Migrations succeed from empty and previous supported schemas.
- Production containers and Vercel builds succeed reproducibly.
- No serious/critical axe violations exist in principal pages.
- Keyboard, focus, zoom, contrast, reduced motion, and screen-reader ordering have been manually checked against the documented WCAG 2.2 AA target.

### Portfolio assets

- README architecture, screenshots, setup, tests, decisions, trade-offs, demo, and video are complete.
- Interview/demo guide covers quotas, caching, async workers, ownership, synchronization, deployment, authentication, and recovery.
- GitHub metadata/social preview are configured.
- The final changelog and `v1.0.0` release are published with pinned container images.

## 14. Fixed assumptions and intentional trade-offs

- Keep SvelteKit and FastAPI; do not rewrite the frontend in Next.js.
- Vercel is the safe demo, while Docker is the complete reference product.
- Maintain one source branch and use configuration rather than a demo branch.
- Use Neon for hosted PostgreSQL; Redis remains required only by full Docker mode.
- Hosted registration, import, channel mutation, and manual external refresh are disabled to protect shared state and YouTube quota.
- OAuth and CSV import are full-mode features. CSV keeps OAuth credentials optional for self-hosters.
- OAuth is one-shot in v1.0; no Google refresh token is stored.
- Watch Later is an application-owned system playlist identified by a stable key.
- Folders categorize channels; tags categorize channels/videos; playlists are ordered video collections.
- Target WCAG 2.2 AA.
- Treat the Vercel Hobby cron limit as a deliberate demo constraint: daily refresh/reset with no timing guarantee inside the hour. Do not pretend it offers the full worker behavior.
- Favor reliability, observable failure, and a polished demonstration over adding unrelated features after the listed acceptance criteria are satisfied.
