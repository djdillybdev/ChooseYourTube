# ChooseYourTube

A self-hostable web app for following and watching YouTube channels. Functions much like an RSS Feed Reader but solely for YouTube Videos.
Watch videos and follow your favorite channels without any other distractions like comments or video recommendations.

## Why did I make this?

YouTube is great, and I find lots of interesting and helpful videos there. But over the years I have become disatisfied with some aspects of it.
The home page is filled with recommendations from channels I am not subscribed to, and these recommendations are constantly changing based on recent activity. While sometimes I find a new interesting video, often I know what I would like to watch. The subscriptions view is useful, but still has now way to filter and just shows all of the channels I am subscribed to.
I wanted an easy way to organize and view the channels I watch. I am aware of extensions like PocketTube that accomplish something similar, but I wanted something that I could customize more and also eliminate other distractions. There are also other features I have in mind to add that this project will enable me to do, such as different ways of randomly picking a video to watch and trying to emulate the experience of channel surfing on old tv channels.

## Tech Stack

- Svelte and TypeScript for frontend
- FastAPI, Postgres, Redis for the backend

ChooseYourTube is GPL-3.0-only licensed and currently targets Python 3.12, Node.js 22+, and pnpm 10.33.0.

## Runtime Modes

- `APP_MODE=full` enables registration, Redis/arq jobs, and live YouTube synchronization for self-hosting.
- `APP_MODE=demo` disables registration and background jobs by default and can start from seeded data without Redis or a YouTube API key.

`APP_ENV=production` enables strict validation for secrets, CORS origins, and OAuth transport. See `.env.example` for the complete typed configuration surface.

### Subscription imports

Full mode can import subscriptions from a Google Takeout CSV without additional credentials. To also enable one-time Google account imports, create a Google OAuth web client, authorize the read-only YouTube Data API scope, and configure:

```env
YOUTUBE_OAUTH_ENABLED=true
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/imports/youtube/oauth/callback
```

The redirect URI must match Google Cloud exactly. OAuth credentials are used only to discover subscriptions and are not persisted; channel metadata and synchronization continue with `YOUTUBE_API_KEY`.

## Quick Start

```bash
YOUTUBE_API_KEY=your-key make quickstart
```

See [deployment and release operations](docs/deployment.md) for the Vercel/Neon demo,
release images, upgrades, backup, restore, and rollback.

## Services

- Frontend (SvelteKit): http://localhost:5173
- Backend API (FastAPI): http://localhost:8000
- Backend docs: http://localhost:8000/docs
- API liveness: http://localhost:8000/health/live
- API readiness: http://localhost:8000/health/ready
- Dev frontend (optional profile): http://localhost:5174
- Dev backend (optional profile): http://localhost:8001

## Notes

- Default runtime mode (lightweight) runs: `frontend`, `backend`, `worker`, `postgres`, `redis`, and a one-shot `migrate` service.
- Migrations are applied automatically before API/worker startup.
- Runtime mode uses production-style images (no reload, no source bind mounts, no `uv` in runtime containers).
- Optional development profile is available when needed:
  - `make dev-up`
  - `make dev-down`
  - `make dev-logs`
- Common commands:
  - `make build`
  - `make up`
  - `make down`
  - `make logs`
  - `make ps`
  - `make migrate`
  - `make test`
  - `make health`
  - `make backup`
  - `CONFIRM=RESTORE BACKUP_FILE=... make restore`
- `cd frontend && pnpm test:e2e:full` runs an isolated seeded stack on ports 5175 and 8002 so it
  can coexist with `make up`. Override those ports with `E2E_FRONTEND_HOST_PORT` and
  `E2E_BACKEND_HOST_PORT` when necessary.
- Reset database/redis volumes with `docker compose --env-file .env down -v`.

## AI Usage

I made use of various coding agents to aid in the development of this project. This usage was mainly in the frontend as that is an area I am less experienced in. I still involved myself in reviewing the code and made architecture and design choices myself.
