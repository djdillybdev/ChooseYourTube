# ChooseYourTube

**A self-hostable, distraction-free YouTube inbox for people who want to choose what they watch.**

[![Try the live demo](https://img.shields.io/badge/Try_the_live_demo-7c3aed?style=for-the-badge)](https://chooseyourtube-demo-tawny.vercel.app)
[![Watch the 2-minute demo](https://img.shields.io/badge/Watch_the_2--minute_demo-334155?style=for-the-badge)](https://github.com/djdillybdev/ChooseYourTube/releases/download/v1.0.0/chooseyourtube-demo-v1.0.0.mp4)

![ChooseYourTube inbox showing a curated feed of followed channels](docs/screenshots/inbox-desktop.png)

[![CI](https://github.com/djdillybdev/ChooseYourTube/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/djdillybdev/ChooseYourTube/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/djdillybdev/ChooseYourTube?display_name=tag)](https://github.com/djdillybdev/ChooseYourTube/releases/latest)
[![License: GPL-3.0-only](https://img.shields.io/badge/license-GPL--3.0--only-blue)](LICENSE)
[![Accessibility: WCAG 2.2 AA target](https://img.shields.io/badge/accessibility-WCAG_2.2_AA_target-0f766e)](docs/accessibility.md)

ChooseYourTube turns selected YouTube channels into a calm, searchable feed. It keeps the useful
parts of subscriptions—new videos, playlists and playback—without recommendations, comments,
trending content or an engagement-driven home page.

The project is also a production-oriented full-stack system: a SvelteKit application talks to a
FastAPI API through a same-origin auth proxy, PostgreSQL stores user-owned state and durable job
history, and Redis/arq runs idempotent synchronization work in the full Docker deployment.

## Live demo

Open the [shared hosted demo](https://chooseyourtube-demo-tawny.vercel.app) and select **Try the
demo**—no credentials are required. You can browse, search, filter, play videos, edit watched state,
and use Watch Later and playlists. External imports, channel mutation and manual YouTube refreshes
are disabled to protect quota and shared data. Mutable demo state resets daily.

The demo is intentionally lighter than the full self-hosted application: Vercel functions and Neon
replace the long-running API/worker stack, and daily maintenance uses public RSS feeds only.

## What it demonstrates

- **Intentional viewing:** a subscription inbox with no recommendation or engagement surfaces.
- **Flexible discovery:** PostgreSQL full-text search plus channel, tag, date, watched and duration
  filters whose state is preserved in the URL.
- **Organization:** icon-based channel categories, cross-cutting tags, favorite channels, ordered
  playlists and a first-class Watch Later list.
- **Subscription onboarding:** Google Takeout CSV and one-time Google OAuth imports with preview,
  deduplication, partial-failure reporting and no retained Google tokens.
- **Observable background work:** durable sync records, counters, safe errors, retry classification,
  active-job deduplication and user-visible activity history.
- **Quota-aware synchronization:** RSS-first change detection, conditional requests and centralized
  YouTube Data API accounting.
- **User-owned data:** every application entity is owner-scoped, with transactional account deletion,
  backup/restore guidance and no persisted Google credentials.
- **Accessible interaction:** keyboard-operable navigation and dialogs, visible focus, live status
  announcements, reduced-motion support and automated axe coverage.

## Product tour

| Browse and combine filters                                                          | Organize a personal library                                                             |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| ![Inbox with the filter panel open](docs/screenshots/filters-desktop.png)           | ![Tag organization settings](docs/screenshots/organization-desktop.png)                 |
| **Watch Later and ordered playback**                                                | **Visible synchronization feedback**                                                    |
| ![Watch Later playlist with saved videos](docs/screenshots/watch-later-desktop.png) | ![Durable synchronization activity and quota status](docs/screenshots/sync-desktop.png) |

## Architecture

[![ChooseYourTube architecture showing the full Docker application and hosted Vercel demo](docs/images/architecture-overview.svg)](docs/architecture.md)

See [Architecture](docs/architecture.md) for request, worker and tenancy flows, and [Engineering
decisions](docs/engineering-decisions.md) for the trade-offs behind them.

## Five-minute Docker quick start

Requirements: Git, Docker with Compose, OpenSSL and a YouTube Data API key.

```bash
git clone https://github.com/djdillybdev/ChooseYourTube.git
cd ChooseYourTube
YOUTUBE_API_KEY=your-key make quickstart
make health
```

Open <http://localhost:5173>, create an account and follow a channel. `make quickstart` creates the
local `.env`, generates a strong auth secret, applies migrations and starts PostgreSQL, Redis, the
API, worker and frontend. Google OAuth credentials are optional because Takeout CSV import is built
in.

For pinned release images, backup, restore, upgrades, Vercel/Neon setup and rollback, use the
[deployment guide](docs/deployment.md).

## Configuration

| Variable                                    | Required   | Default                 | Purpose                                                             |
| ------------------------------------------- | ---------- | ----------------------- | ------------------------------------------------------------------- |
| `APP_ENV`                                   | No         | `local`                 | `local`, `test` or strict `production` validation.                  |
| `APP_MODE`                                  | No         | `full`                  | Selects the complete self-hosted app or restricted shared demo.     |
| `DATABASE_URL`                              | Yes        | Compose-provided        | Async PostgreSQL URL used by the API and worker.                    |
| `DATABASE_POOL_MODE`                        | No         | `persistent`            | `persistent`, `serverless` or Neon `fluid` connection behavior.     |
| `REDIS_URL`                                 | Full mode  | Compose-provided        | Queue and heartbeat storage when background jobs are enabled.       |
| `YOUTUBE_API_KEY`                           | Full mode  | —                       | YouTube Data API key; deliberately absent from the hosted demo.     |
| `AUTH_SECRET`                               | Yes        | Generated locally       | Session signing secret; production requires at least 32 characters. |
| `API_ORIGIN`                                | No         | `http://localhost:5173` | Canonical browser-facing origin.                                    |
| `API_CORS_ORIGINS`                          | No         | `API_ORIGIN`            | Comma-separated trusted frontend origins.                           |
| `REGISTRATION_ENABLED`                      | No         | Mode-derived            | Enables account registration.                                       |
| `BACKGROUND_JOBS_ENABLED`                   | No         | Mode-derived            | Enables Redis/arq scheduling and refresh commands.                  |
| `YOUTUBE_DAILY_QUOTA_BUDGET`                | No         | `8000`                  | Stops optional API work at the configured daily unit budget.        |
| `YOUTUBE_OAUTH_ENABLED`                     | No         | Credential-derived      | Enables one-time Google subscription discovery.                     |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth only | —                       | Google web OAuth client credentials.                                |
| `GOOGLE_REDIRECT_URI`                       | OAuth only | —                       | Exact authorized callback URI.                                      |
| `ALLOW_INSECURE_OAUTH_TRANSPORT`            | Local only | `false`                 | Allows an HTTP OAuth callback during local development.             |
| `DEMO_LOGIN_ENABLED`                        | Demo only  | Mode-derived            | Exposes one-click login for the configured shared account.          |
| `DEMO_USER_EMAIL`                           | Demo only  | —                       | Seeded non-superuser account used by demo sessions.                 |
| `CRON_SECRET`                               | Demo only  | —                       | Protects Vercel daily maintenance; 32+ characters.                  |
| `DEMO_MAINTENANCE_SECRET`                   | No         | —                       | Legacy non-Vercel fallback for `CRON_SECRET`.                       |
| `ACCESS_TOKEN_TTL_SECONDS`                  | No         | `900`                   | Access-token lifetime.                                              |
| `REFRESH_TOKEN_TTL_SECONDS`                 | No         | `2592000`               | Rotating refresh-session lifetime.                                  |
| `SHORTS_MAX_SECONDS`                        | No         | `60`                    | Maximum duration classified as a Short.                             |
| `ENABLE_STARTUP_SCHEMA_CHECK`               | No         | `true`                  | Verifies required migrations during persistent startup.             |
| `ECHO_SQL` / `DEBUG_LOGS`                   | No         | `false`                 | Local diagnostics; avoid verbose production logging.                |
| `WEB_CONCURRENCY` / `GUNICORN_TIMEOUT`      | No         | `2` / `60`              | Docker API process tuning.                                          |

Start with [`.env.example`](.env.example). Compose supplies internal database and Redis URLs; hosted
deployments must provide them explicitly.

## Development and testing

```bash
# Everything suitable for a normal local validation pass
make test

# Backend
cd backend
uv sync --frozen
uv run ruff check app tests scripts
uv run mypy app
uv run pytest

# Frontend
cd frontend
pnpm install --frozen-lockfile
pnpm run api:check
pnpm run check
pnpm run lint
pnpm run test:coverage
pnpm run test:e2e
```

GitHub Actions also builds both production containers, verifies migrations and the generated OpenAPI
contract, runs Playwright against deterministic seeded environments, and scans principal routes with
axe. Backend coverage is gated at 80%; frontend coverage is gated at 70%.

## Engineering trade-offs

- RSS detects likely changes cheaply; full mode uses the Data API for metadata, while the hosted demo
  stays RSS-only to protect quota.
- PostgreSQL is both the application source of truth and durable cache. Content is duplicated per
  owner, favoring isolation and deletion simplicity over storage efficiency.
- Redis/arq performs asynchronous work, but PostgreSQL sync records—not queue results—provide durable
  progress and recovery evidence.
- OAuth tokens are discarded immediately after subscription discovery. CSV remains the lower-trust,
  privacy-friendly import path.
- The Vercel demo trades hourly workers and write-heavy integrations for a reliable free-tier
  showcase. It shares the same services, models and migrations as Docker rather than using a demo
  branch.
- PostgreSQL full-text search improves relevance and performance at the cost of database portability.

The complete rationale is in [Engineering decisions](docs/engineering-decisions.md).

## Security, privacy and ownership

Access and refresh tokens are held in HTTP-only cookies at the SvelteKit boundary. Refresh sessions
rotate, application data is owner-scoped, user-visible errors omit upstream secrets, and structured
logs carry correlation IDs. Google access tokens and uploaded CSV files are not retained after
subscription discovery. Self-hosters control their database, API key and backups.

See [Security policy](SECURITY.md), [Accessibility](docs/accessibility.md), [Contributing](CONTRIBUTING.md)
and [Changelog](CHANGELOG.md).

## AI assistance

Coding agents assisted with implementation, test generation, documentation and frontend iteration.
I defined the product direction and architecture, reviewed and integrated the changes, made the final
engineering decisions, and verified behavior through automated and manual testing. The commit history
and release documentation preserve that reviewable engineering trail.

## License

ChooseYourTube is distributed under the [GNU General Public License v3.0 only](LICENSE).
