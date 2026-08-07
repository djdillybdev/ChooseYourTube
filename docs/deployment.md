# Deployment and self-hosting

The recommended installation runs SvelteKit, FastAPI, PostgreSQL, Redis, and an arq worker with Docker
Compose. A separate Vercel and Neon configuration powers the public demo; it is documented at the end
of this guide for project maintainers.

## Requirements

A small personal installation should have:

- Git;
- Docker Engine with Docker Compose;
- OpenSSL;
- a [YouTube Data API key](https://developers.google.com/youtube/v3/getting-started);
- about 2 CPU cores, 2 GB RAM, and 10 GB of persistent storage.

PostgreSQL data is stored in the `postgres_data` Docker volume. Redis queue state is stored in
`redis_data`.

## Quick installation

```bash
git clone https://github.com/djdillybdev/ChooseYourTube.git
cd ChooseYourTube
YOUTUBE_API_KEY=your-key make quickstart
```

`make quickstart` performs the following work:

1. Copies `.env.example` to `.env` when no local environment file exists.
2. Generates a random 64-character `AUTH_SECRET` when the example value is still present.
3. Saves the `YOUTUBE_API_KEY` supplied on the command line. In an interactive terminal, it can also
   prompt for the key.
4. Applies all Alembic migrations.
5. Builds and starts the application, then runs the health check.

Open <http://localhost:5173> and create an account. The API listens on <http://localhost:8000>, and
interactive API documentation is available at <http://localhost:8000/docs>.

Check or stop the installation with:

```bash
make health
make logs
make ps
make down
```

`make down` removes the containers and network but keeps both data volumes.

## Configuration

Edit `.env` before exposing the application outside your machine. At minimum:

```env
APP_ENV=production
APP_MODE=full
YOUTUBE_API_KEY=<your YouTube Data API key>
AUTH_SECRET=<random value with at least 32 characters>
API_ORIGIN=https://tube.example.com
API_CORS_ORIGINS=https://tube.example.com
```

Generate a new secret with `openssl rand -hex 32`. Keep `.env` outside version control and restrict
access to the host account that runs Docker.

### Configuration reference

| Variable                                    | Required   | Default                 | Purpose                                                            |
| ------------------------------------------- | ---------- | ----------------------- | ------------------------------------------------------------------ |
| `APP_ENV`                                   | No         | `local`                 | Selects `local`, `test`, or strict `production` validation.        |
| `APP_MODE`                                  | No         | `full`                  | Selects the full application or restricted shared demo.            |
| `DATABASE_URL`                              | Yes        | Compose-provided        | Async PostgreSQL URL for the API and worker.                       |
| `DATABASE_POOL_MODE`                        | No         | `persistent`            | Selects persistent, serverless, or Neon fluid connection behavior. |
| `REDIS_URL`                                 | Full mode  | Compose-provided        | Redis queue and worker-heartbeat URL.                              |
| `YOUTUBE_API_KEY`                           | Full mode  | none                    | YouTube Data API key.                                              |
| `AUTH_SECRET`                               | Yes        | generated locally       | Token-signing secret; production requires at least 32 characters.  |
| `API_ORIGIN`                                | No         | `http://localhost:5173` | Browser-facing frontend origin.                                    |
| `API_CORS_ORIGINS`                          | No         | `API_ORIGIN`            | Comma-separated frontend origins trusted by FastAPI.               |
| `REGISTRATION_ENABLED`                      | No         | mode-derived            | Allows new account registration.                                   |
| `REGISTRATION_EMAIL_ALLOWLIST`              | No         | empty                   | Comma-separated exact emails; empty allows any email to register.  |
| `REGISTRATION_ALLOWLIST_REQUIRED`           | No         | `false`                 | Refuses to start with enabled, open registration.                  |
| `BACKGROUND_JOBS_ENABLED`                   | No         | mode-derived            | Enables Redis jobs and scheduled refreshes.                        |
| `YOUTUBE_DAILY_QUOTA_BUDGET`                | No         | `8000`                  | Stops optional API work at this daily unit count.                  |
| `YOUTUBE_OAUTH_ENABLED`                     | No         | credential-derived      | Enables one-time Google subscription discovery.                    |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth only | none                    | Google web OAuth client credentials.                               |
| `GOOGLE_REDIRECT_URI`                       | OAuth only | none                    | Exact authorized Google OAuth callback URI.                        |
| `ALLOW_INSECURE_OAUTH_TRANSPORT`            | Local only | `false`                 | Permits an HTTP OAuth callback during local development.           |
| `DEMO_LOGIN_ENABLED`                        | Demo only  | mode-derived            | Enables one-click access to the configured shared account.         |
| `DEMO_USER_EMAIL`                           | Demo only  | none                    | Email address for the seeded shared account.                       |
| `CRON_SECRET`                               | Demo only  | none                    | Protects Vercel maintenance requests; use 32+ characters.          |
| `DEMO_MAINTENANCE_SECRET`                   | No         | none                    | Legacy non-Vercel fallback for `CRON_SECRET`.                      |
| `ACCESS_TOKEN_TTL_SECONDS`                  | No         | `900`                   | Access-token lifetime in seconds.                                  |
| `REFRESH_TOKEN_TTL_SECONDS`                 | No         | `2592000`               | Refresh-session lifetime in seconds.                               |
| `SHORTS_MAX_SECONDS`                        | No         | `60`                    | Maximum duration classified as a Short.                            |
| `ENABLE_STARTUP_SCHEMA_CHECK`               | No         | `true`                  | Checks required migrations during persistent startup.              |
| `ECHO_SQL` / `DEBUG_LOGS`                   | No         | `false`                 | Local diagnostic logging; leave disabled in production.            |
| `WEB_CONCURRENCY` / `GUNICORN_TIMEOUT`      | No         | `2` / `60`              | API worker count and request timeout for Docker.                   |

Compose supplies its own internal database and Redis URLs. Hosted deployments must set them
explicitly.

### Google OAuth import

OAuth is optional because users can import a Google Takeout CSV. To enable OAuth, create a Google web
OAuth client and configure these values:

```env
YOUTUBE_OAUTH_ENABLED=true
GOOGLE_CLIENT_ID=<client ID>
GOOGLE_CLIENT_SECRET=<client secret>
GOOGLE_REDIRECT_URI=https://api.tube.example.com/imports/youtube/oauth/callback
```

The redirect URI must exactly match the URI registered in Google Cloud. The default local Docker
callback is `http://localhost:8000/imports/youtube/oauth/callback`; local HTTP also requires
`ALLOW_INSECURE_OAUTH_TRANSPORT=true`. ChooseYourTube discards Google tokens after discovering the
subscription list.

## Public deployment

Place a TLS-terminating reverse proxy in front of the frontend and set `API_ORIGIN` and
`API_CORS_ORIGINS` to its exact HTTPS origin. Forward browser traffic to port 5173. Browser API calls
continue through SvelteKit, so the FastAPI port does not need to be publicly exposed. Compose
publishes port 8000 by default; restrict it with the host firewall when the server is reachable from
the internet.

Google OAuth is the exception. When it is enabled, the configured callback URL must reach FastAPI
over HTTPS. Route that exact callback path to port 8000 through the reverse proxy, or use a dedicated
API hostname such as `api.tube.example.com`. Do not expose the unencrypted container port directly.

Do not expose PostgreSQL or Redis. Keep `.env`, backups, API keys, and OAuth credentials readable only
by administrators. Use a unique `AUTH_SECRET` for each installation and retain off-host database
backups.

For a source-built HTTPS deployment on an Oracle Cloud Ubuntu VM, including Caddy and a single setup
command, follow [Deploy on an Oracle Cloud VM](oracle-vm.md).

After changing the public origin, recreate the affected containers:

```bash
docker compose --env-file .env up -d --build
make health
```

## Release images

Tagged releases publish Linux `amd64` and `arm64` images to GHCR. Copy the example environment file,
set the required secrets, and select an exact version:

```bash
cp .env.example .env
# Edit YOUTUBE_API_KEY, AUTH_SECRET, API_ORIGIN, and API_CORS_ORIGINS.
CHOOSEYOURTUBE_VERSION=1.0.0 make release-pull
CHOOSEYOURTUBE_VERSION=1.0.0 make release-up
make health
```

The release compose override uses:

- `ghcr.io/djdillybdev/chooseyourtube-backend:<version>`
- `ghcr.io/djdillybdev/chooseyourtube-frontend:<version>`

Use an exact version instead of `latest` so upgrades and rollbacks remain deliberate.

## Backups and restores

Create a consistent, custom-format PostgreSQL dump:

```bash
make backup
```

The backup script writes to `backups/`. Copy important backups off the Docker host and test restores
on a separate installation.

Restore a selected dump with explicit confirmation:

```bash
BACKUP_FILE=backups/chooseyourtube-20260715T120000Z.dump CONFIRM=RESTORE make restore
```

A restore is destructive. It stops application writers, recreates the database, restores the dump,
applies current migrations, and restarts the services. Data created after the backup is lost.

## Upgrades and rollback

Before an upgrade:

1. Read the release notes and migration notes.
2. Run `make backup` and copy the resulting dump off-host.
3. Pull the exact new image version or source revision.
4. Run `make migrate` before starting code that requires the new schema.
5. Start the services and run `make health`.
6. Check `make logs` for migration, worker, authentication, and synchronization errors.

An application rollback is safe only when the previous version understands the current database
schema. Restore the pre-upgrade backup when a migration is not backward-compatible.

## Reset an installation

`make down` preserves data. To delete the PostgreSQL and Redis volumes as well, run:

```bash
docker compose --env-file .env down --volumes
```

This command permanently removes local application data unless it has been backed up.

## Troubleshooting

### Quick start requests an API key

Supply the key on the command line in non-interactive environments:

```bash
YOUTUBE_API_KEY=your-key make quickstart
```

If `.env` already exists, verify that `YOUTUBE_API_KEY` is not empty or set to `replace-me`.

### A service is unhealthy

Run `make ps`, then inspect logs with `make logs`. PostgreSQL and Redis must be healthy before the
migration, API, worker, and frontend services can start. The API exposes `/health/live` and
`/health/ready` on port 8000.

### The worker is not ready

The worker writes a heartbeat to Redis. Confirm that Redis is healthy, `BACKGROUND_JOBS_ENABLED=true`,
and the worker can read the same `REDIS_URL` as the API.

The worker also reconciles PostgreSQL synchronization records with Redis when it starts and every
five minutes. Queued runs whose ARQ payloads expired are recreated with the same job ID. A run left in
progress for more than ten minutes is marked failed with `WORKER_INTERRUPTED`; the next scheduled or
manual channel refresh creates its replacement. Check for `sync_reconciliation_completed` and
`sync_reconciliation_enqueue_failed` in worker logs when diagnosing queue drift.

### Registration or refresh is disabled

Normal self-hosted installations use `APP_MODE=full`, `REGISTRATION_ENABLED=true`, and
`BACKGROUND_JOBS_ENABLED=true`. Restricted demo settings intentionally disable these operations.

### OAuth callback fails

Check that `GOOGLE_REDIRECT_URI` is identical in `.env` and Google Cloud, including scheme, host,
port, and path. Do not enable insecure OAuth transport on a public deployment.

## Hosted Vercel and Neon demo

This section documents the portfolio demo operated by the project maintainer. It is not a substitute
for the full self-hosted worker architecture.

The demo uses two Vercel projects and a Neon PostgreSQL database:

| Project               | Root directory | Framework/runtime     |
| --------------------- | -------------- | --------------------- |
| `chooseyourtube-api`  | `backend/`     | FastAPI / Python 3.12 |
| `chooseyourtube-demo` | `frontend/`    | SvelteKit             |

The Neon project runs in AWS US East (Northern Virginia). Both Vercel functions use Washington, D.C.
(`iad1`) to keep database traffic in the same region. `backend/vercel.json` configures the API region
and a daily maintenance request at `0 4 * * *` UTC.

### Neon connections

Create separate production and preview branches. Runtime functions use a pooled async URL:

```text
postgresql+asyncpg://USER:PASSWORD@ENDPOINT-pooler.REGION.aws.neon.tech/DATABASE?ssl=require
```

Migrations and database exports use a direct synchronous URL:

```text
postgresql+psycopg2://USER:PASSWORD@ENDPOINT.REGION.aws.neon.tech/DATABASE?sslmode=require
```

Keep the direct URL in the GitHub `NEON_DIRECT_DATABASE_URL` environment secret. Do not set it as the
Vercel runtime `DATABASE_URL` or expose either URL to the frontend. If a Vercel integration manages
database variables, confirm that it does not replace the async runtime URL with a generic
`postgresql://` value.

### Backend environment

Configure Preview and Production separately with their matching Neon branches and frontend aliases:

```env
APP_ENV=production
APP_MODE=demo
DATABASE_URL=<pooled async Neon URL>
DATABASE_POOL_MODE=fluid
API_ORIGIN=https://<frontend-alias>.vercel.app
API_CORS_ORIGINS=https://<frontend-alias>.vercel.app
AUTH_SECRET=<random 32+ character secret>
CRON_SECRET=<different random 32+ character secret>
DEMO_USER_EMAIL=demo@your-domain.example
REGISTRATION_ENABLED=false
BACKGROUND_JOBS_ENABLED=false
YOUTUBE_OAUTH_ENABLED=false
DEMO_LOGIN_ENABLED=true
ENABLE_STARTUP_SCHEMA_CHECK=false
```

Do not configure `YOUTUBE_API_KEY` for the demo. Daily maintenance uses public RSS feeds and does not
call the quota-metered Data API. Vercel sends `CRON_SECRET` as a bearer token to cron endpoints.
`DEMO_MAINTENANCE_SECRET` remains available only as a legacy fallback outside Vercel.

The frontend requires one variable:

```env
API_BASE_URL=https://<backend-alias>.vercel.app
```

### First deployment

1. Create Neon production and preview branches and save both pooled and direct URLs.
2. Import the repository twice in Vercel, select the root directories above, and configure each
   environment.
3. Deploy once to establish stable aliases.
4. Add the direct production URL to the `NEON_DIRECT_DATABASE_URL` GitHub environment secret. Run the
   **Production database migration** workflow with confirmation `MIGRATE`.
5. Seed the demo from a trusted workstation:

   ```bash
   cd backend
   APP_ENV=production APP_MODE=demo \
   DATABASE_URL='<pooled async URL>' DATABASE_POOL_MODE=fluid \
   AUTH_SECRET='<auth secret>' CRON_SECRET='<cron secret>' \
   DEMO_USER_EMAIL='demo@your-domain.example' \
   UV_CACHE_DIR=/tmp/chooseyourtube-uv-cache uv run python -m scripts.seed_demo
   ```

6. Redeploy or promote the backend, then the frontend. Do not migrate or seed during a Vercel build.
7. Verify health, login, inbox, search, and Watch Later:

   ```bash
   python3 scripts/smoke_demo.py \
     --frontend https://<frontend-alias>.vercel.app \
     --backend https://<backend-alias>.vercel.app
   ```

8. Confirm the cron in the backend project's settings. A manual invocation requires the cron secret:

   ```bash
   curl --fail -H "Authorization: Bearer $CRON_SECRET" \
     https://<backend-alias>.vercel.app/internal/demo/maintenance
   ```

The seed provides a fixed seven-channel catalog with deterministic categories, tags, favorites,
watched state, playlists, and representative import and synchronization history. RSS does not provide
video durations, so seeded duration data remains unknown.

Daily maintenance restores mutable state, removes catalog additions, expires old sessions, and makes a
bounded RSS refresh. A `partial` result means the reset succeeded but one or more feeds failed. A
`failed` result means the canonical reset failed. Existing seeded data remains available when a feed
is unavailable.

### Demo rollback and monitoring

Apply migrations before backend code that requires them. Vercel can roll back the frontend and API
independently only when the previous code supports the current schema. An instant rollback does not
restore cron settings, so verify the active schedule afterward.

Monitor function duration and invocation counts, Neon pooled connections and storage, RSS failures,
`/health/ready`, and maintenance `sync_runs`. Logs may contain request and synchronization IDs, but
must not contain credentials, tokens, connection strings, or upstream response bodies.

Deploying a new seed definition does not modify existing rows. Run the trusted-workstation seed
command after promoting the backend, then use `scripts/smoke_demo.py` to verify the catalog.
