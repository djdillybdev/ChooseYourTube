# Changelog

All notable changes are documented here. The project follows [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-07-17

### Added

- One-click hosted demo backed by Vercel and Neon with deterministic daily reset.
- Durable synchronization runs with progress, classified failure, retry and quota visibility.
- RSS-first refresh, conditional requests, API usage accounting and all-channel hourly scheduling.
- Watch Later, ordered playlists, category and tag organization, favorites and duration filtering.
- Google Takeout CSV and one-time Google OAuth subscription imports with preview and partial recovery.
- Responsive SvelteKit interface, accessible dialogs/navigation/status feedback and axe coverage.
- Parallel CI for backend, frontend, OpenAPI drift, browser accessibility and production containers.
- Docker quick start, pinned GHCR release images, backup/restore and Vercel/Neon operations.

### Changed

- Refresh commands use asynchronous `202 SyncRunOut` contracts.
- API errors use stable safe codes, request IDs and retryability instead of arbitrary detail payloads.
- Runtime behavior is selected through validated full/demo settings from one shared codebase.

### Security

- Rotating refresh sessions stay in HTTP-only cookies behind the same-origin SvelteKit proxy.
- Google OAuth tokens and uploaded Takeout files are discarded after subscription discovery.
- Demo registration, imports, channel mutation and external refresh are enforced as disabled server-side.

### Known trade-offs

- The hosted demo uses daily RSS-only maintenance and does not include the full hourly Redis/arq worker.
- Video/channel data is duplicated per owner to favor isolation and straightforward deletion.
- YouTube iframe internals are controlled by a third party and cannot be made fully auditable by the app.

[1.0.0]: https://github.com/djdillybdev/ChooseYourTube/releases/tag/v1.0.0
