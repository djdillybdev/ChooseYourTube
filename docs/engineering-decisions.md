# Engineering decisions

This document records the choices that most affect operation, maintenance, and future development.
Each section includes the cost accepted with the decision.

## Check RSS before using the Data API

Public YouTube feeds are checked before full mode spends Data API quota. Conditional requests use
`ETag` and `Last-Modified` values to reduce work when a channel has not changed. The Data API fills
metadata gaps in batches only when needed. Demo mode does not construct the quota-metered client.

Cost: RSS exposes less metadata and can change independently of the Data API. Parsers need defensive
validation, and the demo cannot guarantee complete durations or playlist metadata.

## Keep durable job state in PostgreSQL

PostgreSQL stores synchronization and import lifecycles alongside user data and API accounting. Redis
contains queued messages and the worker heartbeat. Restarting Redis may delay work, but it does not
remove the last visible status or previously synchronized content.

Cost: workers perform additional database writes for progress and counters.

## Store channel and video data per owner

Channels and videos belong to one account instead of a shared global catalog. Queries, exports, and
account deletion follow the same ownership rule, and one user's changes cannot alter another user's
records.

Cost: popular content consumes repeated storage and refresh work. A shared catalog would need
reference counting, refresh ownership, and more complex deletion rules.

## Use Google OAuth only for discovery

Google OAuth discovers subscription channel IDs. Access and refresh credentials are discarded after
candidate collection, and committed channels use the application's API key. Google Takeout CSV offers
an import path without OAuth.

Cost: ChooseYourTube cannot continuously mirror Google subscription changes. Users must run another
import when their subscription list changes.

## Make background jobs durable and idempotent

Each background command creates a PostgreSQL sync record and uses its UUID as the queue job ID.
The worker reconciles queued records with Redis at startup and every five minutes. Re-enqueueing the
same UUID is idempotent, so a Redis restart or an expired ARQ payload cannot leave a channel
permanently queued. Runs left in progress beyond the worker timeout and safety margin are recorded as
`WORKER_INTERRUPTED`; channel refreshes are replaced by the next scheduled or manual refresh, while
other retryable work can use the existing retry endpoint.
An explicit manual request promotes an already-deferred job to run immediately without changing its
durable sync-run ID.
Active-run deduplication, unique source identifiers, and upserts make duplicate delivery safe. Retry
policy distinguishes temporary failures from invalid configuration, authorization, and quota limits.

Cost: the orchestration code is more explicit than a fire-and-forget task, and each batch must update
durable progress correctly.

## Run arq and Redis in full mode

Synchronization and imports can outlive an HTTP request, so the full installation uses arq for queued
execution, retry scheduling, and hourly channel refresh. The worker heartbeat contributes to API
readiness.

Cost: self-hosters operate Redis and a separate worker process. Demo mode omits both because Vercel
does not provide a persistent worker.

## Share code between full and demo modes

Both deployments use the same services, API schemas, migrations, and frontend components. Validated
settings and backend policy gates define the restricted demo behavior.

Cost: the interface must explain unavailable demo actions, and services must remain valid with the
demo's smaller infrastructure set.

## Restrict the public demo

The Vercel and Neon demo uses one-click access, daily state reset, and RSS-only maintenance. It allows
safe library interactions while disabling registration, imports, channel changes, and manual refresh.

Cost: visitors cannot observe the persistent worker live. Seeded job history and the architecture
documentation show the full-mode behavior without risking shared data, quota, or free-tier resources.

## Use PostgreSQL full-text search

Video search uses a GIN-backed PostgreSQL full-text expression instead of a portable substring scan.
This improves relevance and query performance for a growing library.

Cost: search is tied to PostgreSQL. The application already requires PostgreSQL for its durable data
and job model, so database portability is not a current goal.
