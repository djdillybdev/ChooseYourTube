# ChooseYourTube frontend

Svelte 5 and SvelteKit frontend for the ChooseYourTube distraction-free YouTube inbox. The root
[README](../README.md) is the primary product, architecture and self-hosting guide; this document
covers frontend development.

## Responsibilities

- Server-rendered application routes for the inbox, channels, categories, playlists and settings.
- Same-origin authentication and API proxy routes that keep access and refresh tokens in HTTP-only
  cookies.
- URL-backed search, watched, date, duration, channel and tag filters.
- Accessible responsive navigation, dialogs, status feedback and media controls.
- Node adapter builds for Docker and Vercel adapter builds for the hosted demo.

Shared UI, API clients, stores, server auth helpers and types live in `src/lib/`. Pages and SvelteKit
server endpoints live in `src/routes/`. Vitest tests are split between server and component projects;
Playwright covers browser workflows and full-stack contracts.

## Local development

Requirements: Node.js 22 or newer, pnpm 10.33.0, and a running ChooseYourTube API. From this
directory:

```bash
pnpm install --frozen-lockfile
cp .env.example .env.local
pnpm dev
```

The default backend is <http://localhost:8000>. Set `API_BASE_URL` or `VITE_API_BASE_URL` when it is
available elsewhere; `API_BASE_URL` is preferred for server deployments. Browser requests still go
through SvelteKit rather than calling FastAPI directly.

For the complete development stack with PostgreSQL, Redis and a worker, run `make dev-up` from the
repository root instead.

## Build targets

```bash
pnpm build          # adapter-node production build used by Docker
pnpm build:vercel   # adapter-vercel build used by the hosted demo
pnpm preview        # preview the most recent production build
```

`svelte.config.js` selects the Vercel adapter when `VERCEL=1` or `DEPLOY_TARGET=vercel`; otherwise it
uses the Node adapter.

## API contract

The backend OpenAPI document is the source of truth. After changing a backend router or schema:

```bash
pnpm api:generate
pnpm api:check
```

The first command regenerates `openapi.json` and `src/lib/types/generated.ts`; the second verifies
that both checked-in files are current without rewriting them. Do not edit generated files manually.
Frontend-only aliases and filter types belong in `src/lib/types/api.ts`.

## Validation

```bash
pnpm check
pnpm lint
pnpm test:coverage
pnpm test:e2e:fast   # deterministic browser suite with the fake backend
pnpm test:e2e:full   # Docker-backed frontend/backend integration suite
pnpm docs:check      # public documentation links and placeholders
```

`pnpm test:e2e` runs both browser suites. Frontend coverage thresholds are 70%; principal browser
routes also run automated axe checks for serious and critical accessibility violations.

Portfolio screenshots and video are reproducible workflows documented in
[`docs/screenshots/README.md`](../docs/screenshots/README.md) and
[`docs/demo-script.md`](../docs/demo-script.md).
