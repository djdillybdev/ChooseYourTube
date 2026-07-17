# Changelog

This file records user-visible changes to ChooseYourTube. Releases follow
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-07-17

### Added

- One-click hosted demo on Vercel and Neon with a deterministic daily reset.
- Synchronization records with progress, classified failures, retry state, and quota use.
- RSS-first refresh, conditional requests, API usage accounting, and hourly channel scheduling.
- Watch Later, ordered playlists, categories, tags, favorites, and duration filters.
- Google Takeout CSV and one-time Google OAuth imports with preview and partial-failure handling.
- Responsive SvelteKit interface with keyboard-operable navigation, dialogs, and status feedback.
- CI checks for backend and frontend code, OpenAPI drift, browser accessibility, and containers.
- Docker quick start, pinned GHCR images, database backup and restore, and Vercel operations.

### Changed

- Refresh commands now return asynchronous `202 SyncRunOut` responses.
- API errors now return stable safe codes, request IDs, and retryability instead of arbitrary detail
  payloads.
- Validated full and demo settings now select runtime behavior from one codebase.

### Security

- Rotating refresh sessions remain in HTTP-only cookies behind the same-origin SvelteKit proxy.
- Google OAuth tokens and uploaded Takeout files are discarded after subscription discovery.
- Demo restrictions on registration, imports, channel changes, and external refresh are enforced by
  the backend.

### Known limitations

- The hosted demo uses daily RSS-only maintenance instead of the full hourly Redis and arq worker.
- Video and channel data is stored per owner to simplify isolation and deletion, which duplicates
  content across accounts.
- The application cannot inspect or change accessibility behavior inside the third-party YouTube
  iframe.

[1.0.0]: https://github.com/djdillybdev/ChooseYourTube/releases/tag/v1.0.0
