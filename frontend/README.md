# ChooseYourTube frontend

This directory contains the Svelte 5 and SvelteKit application. The root [README](../README.md) covers
the product and Docker installation; this guide is for frontend development.

## Responsibilities

The frontend provides:

- server-rendered pages for the inbox, channels, organization, playlists, imports, and settings;
- same-origin authentication and API proxy routes that keep tokens in HTTP-only cookies;
- URL-backed search, channel, category, tag, date, duration, and watched-state filters;
- responsive navigation, dialogs, status announcements, and media controls;
- Node builds for Docker and Vercel builds for the hosted demo.

Application routes and SvelteKit server endpoints live in `src/routes/`. Shared components, API
clients, stores, server helpers, and types live in `src/lib/`. Tests are grouped under `tests/` by
unit, component, and browser scope.

## Requirements

- Node.js 22 or newer
- pnpm 10.33.0
- a running ChooseYourTube API

The complete development stack is available from the repository root with `make dev-up`. For a
standalone frontend process, run these commands from this directory:

```bash
pnpm install --frozen-lockfile
cp .env.example .env.local
pnpm dev
```

The default API URL is <http://localhost:8000>. Set `API_BASE_URL` when the API runs elsewhere.
`VITE_API_BASE_URL` remains available for local compatibility, but server deployments should use
`API_BASE_URL`. Browser requests still pass through SvelteKit rather than calling FastAPI directly.

## Project structure

```text
src/
  lib/
    api/          Backend client wrappers
    components/   Shared Svelte components
    server/       Server-only authentication and request helpers
    stores/       Client state
    types/        Generated API types and frontend aliases
    utils/        Reusable utilities
  routes/         Pages, layouts, form actions, and server endpoints
static/           Public assets
tests/
  unit/           Server and utility tests
  component/      Svelte component tests
  e2e/            Playwright browser tests
```

## Build targets

```bash
pnpm build          # adapter-node build used by Docker
pnpm build:vercel   # adapter-vercel build used by the hosted demo
pnpm preview        # preview the latest production build
```

`svelte.config.js` selects the Vercel adapter when `VERCEL=1` or `DEPLOY_TARGET=vercel`. Other builds
use the Node adapter.

## API contract

The FastAPI OpenAPI document is the source of truth. After changing a backend router or schema:

```bash
pnpm api:generate
pnpm api:check
```

`api:generate` refreshes `openapi.json` and `src/lib/types/generated.ts`. `api:check` confirms that
both checked-in files match the backend without rewriting them. Do not edit generated files by hand.
Frontend-only aliases and filter types belong in `src/lib/types/api.ts`.

## Validation

```bash
pnpm check             # Svelte and TypeScript checks
pnpm lint              # Prettier and ESLint
pnpm test:coverage     # Vitest with 70% coverage thresholds
pnpm test:e2e:fast     # Playwright against the deterministic fake backend
pnpm test:e2e:full     # Docker-backed frontend/API browser tests
pnpm docs:check        # Markdown links and placeholders
```

`pnpm test:e2e` runs both browser suites. Principal browser routes also run axe checks for serious and
critical accessibility violations.

Use the [frontend UI guidelines](../docs/frontend-ui-guidelines.md) when changing shared interactions.
Portfolio capture workflows are documented in the [screenshot guide](../docs/screenshots/README.md)
and [demo guide](../docs/demo-script.md).
