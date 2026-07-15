# Deployment and release operations

ChooseYourTube supports two deployments from the same branch:

- a full Docker installation with PostgreSQL, Redis, API, worker, and SvelteKit;
- a shared recruiter demo with separate SvelteKit and FastAPI Vercel projects and Neon.

The demo is intentionally not the full worker architecture. Vercel Hobby invokes maintenance once
per day and may run it at any point during the configured UTC hour. The durable Neon snapshot remains
usable when maintenance or the public channel feeds are unavailable.

## Full Docker installation

Requirements are Git, Docker with Compose, OpenSSL, and a YouTube Data API key. A small installation
should reserve approximately 2 CPU cores, 2 GB RAM, and 10 GB of persistent disk. PostgreSQL data is
stored in `postgres_data`; Redis queue state is stored in `redis_data`.

```bash
git clone <repository-url>
cd ChooseYourTube
YOUTUBE_API_KEY=your-key make quickstart
make health
```

`make quickstart` creates `.env` when needed, generates `AUTH_SECRET`, applies migrations, and starts
the stack. Google OAuth credentials are optional because Takeout CSV import remains supported.

For a tagged release, use exact-semver GHCR images instead of local builds:

```bash
cp .env.example .env
# Configure YOUTUBE_API_KEY and AUTH_SECRET.
CHOOSEYOURTUBE_VERSION=1.0.0 make release-pull
CHOOSEYOURTUBE_VERSION=1.0.0 make release-up
make health
```

### Backup, restore, upgrade, and reset

```bash
make backup
BACKUP_FILE=backups/chooseyourtube-20260715T120000Z.dump CONFIRM=RESTORE make restore
```

Backups are consistent online custom-format PostgreSQL dumps. Restore is destructive: it stops
application writers, recreates the database, restores the dump, reapplies migrations, and restarts
the services. Keep off-host copies according to the installation's retention policy.

Before upgrading, take a backup, pull the exact new image tag, run `make migrate`, start the services,
and run `make health`. Application rollbacks may use the previous exact image tag only while that
version remains compatible with the deployed schema.

To remove containers but preserve data, run `make down`. The following is a destructive full reset:

```bash
docker compose --env-file .env down --volumes
```

## Vercel and Neon recruiter demo

Use a Neon project in AWS Europe (Frankfurt) and two Vercel projects connected to this repository:

| Project | Root directory | Framework/runtime |
| --- | --- | --- |
| `chooseyourtube-api` | `backend/` | FastAPI / Python 3.12 |
| `chooseyourtube-demo` | `frontend/` | SvelteKit |

The backend is configured in `backend/vercel.json` for `fra1`, a 300-second function limit, and the
daily `0 4 * * *` UTC maintenance request. The frontend selects `adapter-vercel` automatically when
Vercel sets `VERCEL=1`; Docker continues to use `adapter-node`.

### Neon connections

Create a `production` branch and a separate `preview` branch. Obtain both pooled and direct connection
strings for each branch. Runtime URLs must use the async driver and the pooled hostname:

```text
postgresql+asyncpg://USER:PASSWORD@ENDPOINT-pooler.REGION.aws.neon.tech/DATABASE?ssl=require
```

Do not paste Neon's generic `postgresql://` connection string into the Vercel backend unchanged.
That URL selects the synchronous `psycopg2` driver and the Python function will fail during import.
For `DATABASE_URL`, preserve the encoded username, password, pooled hostname, and database name;
change the scheme to `postgresql+asyncpg://` and use the asyncpg-compatible `?ssl=require` query.
If a Neon-Vercel integration also manages environment variables, verify that it is not overwriting the
manually configured `DATABASE_URL` with a generic connection string.

Migrations, `pg_dump`, and restore use the direct hostname and a sync driver:

```text
postgresql+psycopg2://USER:PASSWORD@ENDPOINT.REGION.aws.neon.tech/DATABASE?sslmode=require
```

Keep the direct URL only in the GitHub `NEON_DIRECT_DATABASE_URL` environment secret. Do not set it as
the Vercel backend's `DATABASE_URL` or `ALEMBIC_DATABASE_URL`.

Never expose either URL to the frontend project.

### Backend environment variables

Set these separately for Preview and Production, using the matching Neon branch and frontend alias:

```env
APP_ENV=production
APP_MODE=demo
DATABASE_URL=<pooled async Neon URL>
DATABASE_POOL_MODE=serverless
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

Do not configure `YOUTUBE_API_KEY` for the Vercel backend. Demo maintenance reads the curated
channels' public RSS feeds directly and never calls the quota-metered YouTube Data API.

Vercel automatically sends `CRON_SECRET` as `Authorization: Bearer ...` to cron endpoints. The legacy
`DEMO_MAINTENANCE_SECRET` remains accepted as a fallback outside Vercel, but do not configure two
different values.

The frontend project needs only:

```env
API_BASE_URL=https://<backend-alias>.vercel.app
```

Use stable branch aliases for Preview so frontend and backend previews point to the preview Neon
branch. Production must use only the two production Vercel aliases. Browser traffic remains
same-origin through SvelteKit's `/api/backend/*` proxy.

### First deployment

1. Create the Neon production and preview branches and save pooled/direct URLs securely.
2. Import the repository twice in Vercel, select the root directories above, and configure environment
   variables. Deploy once to establish stable Vercel aliases.
3. Put the direct production URL in the `NEON_DIRECT_DATABASE_URL` GitHub environment secret and run
   the **Production database migration** workflow with confirmation `MIGRATE`.
4. Seed from a trusted workstation using the pooled production URL:

   ```bash
   cd backend
   APP_ENV=production APP_MODE=demo \
   DATABASE_URL='<pooled async URL>' DATABASE_POOL_MODE=serverless \
   AUTH_SECRET='<auth secret>' CRON_SECRET='<cron secret>' \
   DEMO_USER_EMAIL='demo@your-domain.example' \
   UV_CACHE_DIR=/tmp/chooseyourtube-uv-cache uv run python scripts/seed_demo.py
   ```

5. Redeploy/promote the backend, then frontend. Do not run migrations or seeding as a Vercel build
   command.
6. Verify `/health/live`, `/health/ready`, demo login, inbox, search, and Watch Later:

   ```bash
   python3 scripts/smoke_demo.py \
     --frontend https://<frontend-alias>.vercel.app \
     --backend https://<backend-alias>.vercel.app
   ```

7. Confirm the cron appears in the backend project's Cron Jobs settings. A manual safe invocation is:

   ```bash
   curl --fail -H "Authorization: Bearer $CRON_SECRET" \
     https://<backend-alias>.vercel.app/internal/demo/maintenance
   ```

Daily maintenance has a deterministic per-day run ID, refreshes only the four catalog channels for at
most 180 seconds, restores mutable state, and removes expired sessions. `partial` means reset succeeded
but one or more RSS feeds could not be refreshed; `failed` means canonical reset failed. RSS provides
recent video titles, descriptions, publication dates, and thumbnails but not full channel history or
duration/tag metadata. The deterministic seed supplies those richer demo examples and remains usable
when feeds are unavailable.

### Rollback and monitoring

Deploy database migrations before backend code that requires them. Roll back frontend and backend
independently through Vercel only when the previous application understands the current schema. Vercel
instant rollback does not roll back cron configuration, so verify the active cron after a rollback.

During the initial release, monitor Vercel function duration/invocations, Neon pooled connections and
storage, RSS failure rates, `/health/ready`, and maintenance `sync_runs`. Logs should contain
request/sync IDs but never tokens, secrets, database URLs, or upstream response bodies. To reseed, rerun
`scripts/seed_demo.py`; take a Neon export before manual production repairs.
