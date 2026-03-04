# Repository Guidelines

- Follow best practices for Svelte5
- Always use pnpm
- Refer to openapi.json for info about API endpoints of the backend
- Follow TDD

## Project Structure & Module Organization
- Application code lives in `src/`.
- Route pages and API endpoints follow SvelteKit conventions under `src/routes/` (for example, `src/routes/api/auth/login/+server.ts` and `src/routes/channels/[id]/+page.svelte`).
- Shared logic is in `src/lib/`:
  - `api/` for backend client wrappers
  - `components/` for Svelte UI
  - `stores/` for app state
  - `utils/` and `server/` for pure and server-side helpers
- Static files are in `static/`.
- Tests live in `tests/` split by type: `unit/`, `component/`, `e2e/`, plus MSW/setup helpers.

## Build, Test, and Development Commands
- `pnpm run dev`: start local dev server.
- `pnpm run build`: create production build.
- `pnpm run preview`: preview the built app.
- `pnpm run check`: run Svelte sync + type checking.
- `pnpm run lint`: run Prettier check and ESLint.
- `pnpm run format`: auto-format the repository.
- `pnpm run test:unit`: run Vitest server + component projects.
- `pnpm run test:e2e`: run Playwright tests (`tests/e2e`).
- `pnpm run test:coverage`: run Vitest with coverage (70% thresholds for lines/branches/functions/statements).

## Coding Style & Naming Conventions
- TypeScript is strict (`tsconfig.json`), with Svelte 5 and SvelteKit patterns.
- Use tabs, single quotes, trailing commas off, and 100-char line width (see `.prettierrc`).
- Keep route files in SvelteKit naming format (`+page.ts`, `+page.svelte`, `+server.ts`).
- Use `PascalCase.svelte` for components and descriptive camelCase for utility/store modules.

## Testing Guidelines
- Frameworks: Vitest (`node` + `jsdom` projects), Testing Library, MSW, Playwright.
- Name tests `*.spec.ts` or `*.test.ts`; component tests use `*.svelte.spec.ts`.
- Prefer colocated behavior-focused tests under `tests/unit` and `tests/component` matching source domains.
- Run `pnpm run test:ci` before merging when changing critical flows.

## Commit & Pull Request Guidelines
- Prefer Conventional Commit style seen in history, e.g. `feat(auth): add login endpoint` or `refactor: simplify filter parsing`.
- Keep commits focused and atomic; include tests with behavior changes.
- PRs should include:
  - clear summary and motivation
  - linked issue(s) when available
  - test evidence (`pnpm run lint`, `pnpm run test:unit`, and e2e when relevant)
  - screenshots/GIFs for UI changes

## Security & Configuration Tips
- Copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL` for your environment.
- Do not commit secrets or environment-specific credentials.
