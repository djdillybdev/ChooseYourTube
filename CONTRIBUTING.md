# Contributing

Thanks for helping improve ChooseYourTube. Please keep changes focused on intentional subscription
browsing; recommendation, trending and engagement-feed features are outside the product direction.

## Before opening a pull request

1. Open an issue before a large feature or schema change so the approach can be agreed first.
2. Start from `.env.example`; never commit secrets or personal fixture data.
3. Keep frontend HTTP behavior in API clients/routes and backend orchestration in services rather than
   routers.
4. Add regression tests for behavior changes and regenerate the OpenAPI contract after API changes.
5. Update migrations, documentation and screenshots when the public behavior changes.

## Local validation

```bash
make test

cd backend
uv run ruff check app tests scripts
uv run mypy app
uv run pytest

cd ../frontend
pnpm run api:check
pnpm run check
pnpm run lint
pnpm run test:coverage
pnpm run test:e2e
```

Use short imperative commits. Pull requests should explain the motivation, user/developer impact,
implementation, test commands, migrations or configuration changes, and include screenshots for UI
work. By contributing, you agree that your changes are distributed under GPL-3.0-only.

Report vulnerabilities through the private process in [SECURITY.md](SECURITY.md), not a public issue.
