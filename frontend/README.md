# ChooseYourTube frontend

SvelteKit frontend for ChooseYourTube. The root repository README is the primary setup and architecture guide.

## Requirements

- Node.js 22 or newer
- pnpm 10.33.0 (pinned in `package.json`)
- A running ChooseYourTube API, normally at `http://localhost:8000`

## Development

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Set `API_BASE_URL` when the backend is not available at its local default. Browser requests go through SvelteKit server routes so access and refresh tokens remain in HTTP-only cookies.

## API contract

The backend OpenAPI document is the source of truth. Regenerate the checked-in schema and TypeScript types after an API change:

```bash
pnpm api:generate
```

Verify that both generated files are current without rewriting them:

```bash
pnpm api:check
```

Do not edit `openapi.json` or `src/lib/types/generated.ts` manually. Add ergonomic aliases and frontend-only filter types in `src/lib/types/api.ts`.

## Validation

```bash
pnpm check
pnpm lint
pnpm test:coverage
pnpm test:e2e
```
