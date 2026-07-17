# Engineering decisions

This document records the decisions most relevant to operating and discussing ChooseYourTube. They
favor observable failure, user ownership and a credible self-hosted product over maximum abstraction.

## RSS-first synchronization

Public YouTube feeds are checked before full mode spends Data API quota. Conditional `ETag` and
`Last-Modified` requests make no-change refreshes inexpensive; the Data API fills metadata gaps in
batches only when useful. The hosted demo is stricter and never constructs the quota-metered client.

**Trade-off:** RSS exposes less metadata and can change independently of the Data API, so parsers need
defensive validation and the demo cannot promise complete durations or playlist metadata.

## PostgreSQL as durable source of truth

PostgreSQL stores the user library, imports, quota accounting and synchronization lifecycle. Redis is
only queue transport and heartbeat storage. A queue restart can delay work but cannot erase the last
known user-visible status or content.

**Trade-off:** workers perform additional database writes for progress, but failures become inspectable
and recoverable instead of disappearing into logs.

## Per-owner content duplication

Channels and videos are owned records rather than shared global catalog entries. This makes every
query, deletion and export follow one tenancy rule and avoids one user's mutation affecting another.

**Trade-off:** popular content consumes repeated storage and refresh work. A shared catalog could be
more efficient but would require reference counting, shared refresh ownership and more complex privacy
boundaries.

## One-time Google OAuth

Google OAuth is used only to discover subscription channel IDs. Access and refresh credentials are
discarded after candidate collection; committed channels then use the application's API key. Google
Takeout CSV provides an OAuth-free alternative.

**Trade-off:** the app cannot continuously mirror subscription changes, but it retains substantially
less sensitive data and makes credential revocation simpler.

## Durable, idempotent jobs

Every background command creates a PostgreSQL sync record and uses its UUID as the queue job ID.
Active-run deduplication, source-ID uniqueness and upserts make duplicate delivery safe. Retry policy is
bounded and classifies transient failures separately from invalid configuration, authorization and
quota exhaustion.

**Trade-off:** orchestration is more explicit than fire-and-forget tasks, but the UI can show progress,
partial completion and actionable failure history.

## Redis/arq for the full deployment

The full application uses arq because synchronization and imports outlive normal HTTP requests and
benefit from retry scheduling and an hourly cron. A worker heartbeat participates in readiness.

**Trade-off:** self-hosters operate an additional service. Redis becomes optional in demo mode, where
Vercel cannot provide a persistent worker anyway.

## One codebase for demo and full modes

Both deployments share services, schemas, migrations and frontend components. Typed settings and
backend policy gates define the small behavioral difference.

**Trade-off:** some UI must explain disabled features, but fixes cannot silently drift between a demo
branch and the actual product.

## A deliberately constrained hosted demo

The Vercel/Neon demo uses one-click access, daily reset and RSS-only maintenance. It allows safe library
interactions while disabling registration, external imports, channel mutation and manual refresh.

**Trade-off:** recruiters do not see the persistent worker running live. Seeded sync/import history and
the Docker architecture expose the design without risking shared state, quota or free-tier resources.

## PostgreSQL full-text search

Video search uses a PostgreSQL GIN-backed full-text expression for relevance and scale rather than a
portable substring scan.

**Trade-off:** the implementation is database-specific. PostgreSQL is already a deliberate deployment
dependency, so stronger search behavior is worth that coupling.
