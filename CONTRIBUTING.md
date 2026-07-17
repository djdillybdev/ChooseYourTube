# Contributing to ChooseYourTube

ChooseYourTube focuses on intentional subscription viewing. Recommendation feeds, trending modules,
comments, and engagement prompts are outside the product direction.

## Before starting

Open an issue before a large feature, API contract change, or database migration so the approach can
be reviewed. Small fixes can go directly to a focused pull request.

Keep these boundaries in mind:

- SvelteKit pages and server endpoints live in `frontend/src/routes/`; shared frontend code belongs in
  `frontend/src/lib/`.
- FastAPI routers handle HTTP concerns, services coordinate application work, and CRUD modules own
  database queries.
- Database and network boundaries remain explicitly asynchronous.
- User-owned data must be scoped by the authenticated owner.
- Secrets and personal fixture data must not be committed.

## Development setup

Start the bind-mounted stack from the repository root:

```bash
cp .env.example .env
# Set YOUTUBE_API_KEY and replace AUTH_SECRET.
make dev-up
make dev-logs
```

The frontend runs at <http://localhost:5174> and the API at <http://localhost:8001>. Standalone setup
is documented in the [frontend README](frontend/README.md) and [backend README](backend/README.md).

## Tests and generated files

Add regression tests for behavior changes. Run the root validation suite before opening a pull
request:

```bash
make test
```

Run browser tests when a change affects navigation, forms, authentication, API integration, or other
user workflows:

```bash
cd frontend
pnpm test:e2e:fast
pnpm test:e2e:full
```

After changing a backend router or schema, regenerate and verify the OpenAPI contract:

```bash
cd frontend
pnpm api:generate
pnpm api:check
```

Commit both `openapi.json` and `src/lib/types/generated.ts` when they change. Do not edit either file
manually.

## Pull requests

Keep commits focused and use short imperative subjects. A pull request should include:

- the problem and the reason for the change;
- the user or developer impact;
- the main implementation decisions;
- the commands used for validation;
- API, configuration, schema, or migration notes;
- screenshots for visible interface changes.

Update public documentation and portfolio screenshots when behavior changes. By contributing, you
agree that your work is distributed under GPL-3.0-only.

Use the private process in [SECURITY.md](SECURITY.md) for vulnerabilities. Do not include exploitable
details in a public issue.
