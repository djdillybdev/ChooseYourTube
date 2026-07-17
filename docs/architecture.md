# Architecture

ChooseYourTube has one application codebase and two runtime configurations. The full Docker
installation includes background workers and YouTube Data API access. The hosted demo uses the same
models, services, migrations, and frontend components with a restricted set of operations.

## Components

```mermaid
flowchart LR
    Browser -->|HTTP-only session cookies| Proxy[SvelteKit server routes]
    Proxy -->|short-lived bearer token| API[FastAPI routers]
    API --> Services[Application services]
    Services --> CRUD[Owner-scoped data access]
    CRUD --> PG[(PostgreSQL)]
    Services -->|sync-run UUID as job ID| Redis[(Redis)]
    Redis --> Worker[arq worker]
    Worker --> Services
    Services --> RSS[YouTube RSS]
    Services --> YT[YouTube Data API]
```

SvelteKit renders the interface, handles browser-facing authentication, and proxies API requests.
This keeps access and refresh tokens in same-origin HTTP-only cookies.

FastAPI routers validate requests and call application services. Services coordinate data access,
external clients, and background jobs. Async CRUD modules contain database queries.

PostgreSQL stores accounts, channels, videos, categories, tags, playlists, imports, YouTube API usage,
and synchronization history. Redis carries queued work and the worker heartbeat; PostgreSQL remains
the durable record of job status.

## Authenticated request flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant S as SvelteKit
    participant A as FastAPI
    participant P as PostgreSQL

    B->>S: Request with HTTP-only cookies
    S->>A: Forward with short-lived access token
    A->>P: Run owner-scoped query
    P-->>A: Return current user's records
    A-->>S: Return typed response or safe error
    S-->>B: Render page or return JSON
    Note over S,A: SvelteKit attempts one refresh when the access token expires
```

The browser never receives database credentials or Google OAuth tokens. Public API errors contain a
stable code, safe message, request ID, and retryable flag. Detailed exceptions remain in structured
server logs.

## Synchronization flow

```mermaid
sequenceDiagram
    participant U as User or scheduler
    participant A as FastAPI
    participant P as PostgreSQL
    participant R as Redis
    participant W as arq worker
    participant Y as YouTube

    U->>A: Request refresh or import
    A->>P: Create or reuse queued sync run
    A->>R: Enqueue run UUID
    A-->>U: Return 202 with sync run
    R->>W: Deliver job
    W->>P: Claim run and record attempt
    W->>Y: Check RSS, then request API metadata when needed
    W->>P: Upsert data and persist counters
    W->>P: Store succeeded, partial, or failed state
    U->>A: Poll sync run
    A->>P: Read durable state
    A-->>U: Return progress or terminal result
```

The run UUID is also the arq job ID, which prevents duplicate active delivery for the same work.
Workers claim runs atomically. Unique source IDs and upserts make retries safe.

RSS conditional requests use `ETag` and `Last-Modified` values to detect changes before full mode
spends Data API quota. Batch counters are committed as work progresses. Retryable failures use bounded
backoff; configuration, credential, and quota errors do not retry indefinitely.

The scheduler paginates across every followed channel and isolates channel failures. One unavailable
feed therefore does not stop unrelated refreshes. The frontend reads the PostgreSQL sync record and
keeps the last successfully loaded content visible when a refresh fails.

## Data ownership

Core application records include `owner_id`. Routers resolve the authenticated account before calling
services, and CRUD queries scope reads and writes to that owner. An identifier owned by another user
returns the same response as a missing identifier. Account deletion removes owned data in one
transaction.

Channel and video metadata is duplicated for each owner. This increases storage and can repeat refresh
work, but it keeps queries, exports, and deletion within one ownership model. The alternative would
require shared-record lifecycle and reference-counting rules.

## Full Docker installation

```mermaid
flowchart TB
    Browser --> Frontend[SvelteKit with adapter-node]
    Frontend --> API[FastAPI with Gunicorn]
    API --> PG[(PostgreSQL 16)]
    API --> Redis[(Redis 7)]
    Redis --> Worker[arq worker and hourly scheduler]
    Worker --> PG
    Worker --> RSS[YouTube RSS]
    Worker --> YT[YouTube Data API]
    Migrate[Alembic migration service] --> PG
```

This is the reference product configuration. It supports registration, CSV and OAuth imports,
channel changes, manual refresh, hourly scheduling, and quota-accounted Data API metadata.

## Hosted demo

```mermaid
flowchart TB
    Browser --> Frontend[SvelteKit on Vercel]
    Frontend --> API[FastAPI Vercel function]
    API --> Neon[(Neon PostgreSQL)]
    Cron[Vercel daily cron] -->|Bearer secret| API
    API -->|bounded maintenance| RSS[Public YouTube RSS]
```

The shared demo has no Redis service, persistent worker, or YouTube API key. Backend policy disables
registration, imports, channel changes, and manual external refresh. Daily maintenance restores the
seeded state and attempts a bounded RSS update. The last stored dataset remains available when a feed
or maintenance request fails.

See [Deployment and self-hosting](deployment.md) for operational procedures and
[Engineering decisions](engineering-decisions.md) for the trade-offs behind these boundaries.
