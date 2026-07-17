# Portfolio demo and interview guide

Canonical demo: <https://chooseyourtube-demo-tawny.vercel.app>

The shared account needs no credentials and resets daily. Avoid presenting disabled imports or manual
refresh as missing functionality: they are deliberate safeguards for shared state and YouTube quota.

## Two-minute walkthrough

| Time      | On screen                                                      | Caption / narration                                                                                                                                                    |
| --------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0:00–0:10 | Open the demo and select **Try the demo**.                     | “ChooseYourTube is a self-hostable YouTube inbox for intentional viewing—without recommendations, comments or trending feeds.”                                         |
| 0:10–0:30 | Show the populated Inbox and switch between list/grid views.   | “Users follow only the channels they choose. PostgreSQL stores a durable personal library, so browsing does not depend on a live YouTube request.”                     |
| 0:30–0:50 | Open filters, combine a category/tag with search and duration. | “Search uses PostgreSQL full-text indexing, and URL-backed filters combine channel, tag, watched, date and duration state.”                                            |
| 0:50–1:05 | Mark a video watched and save it to Watch Later.               | “Safe optimistic interactions remain owner-scoped. Watch Later is an application-owned system playlist with ordered membership.”                                       |
| 1:05–1:20 | Start playback and show the queue.                             | “The player preserves queue order and exposes failures instead of silently skipping content.”                                                                          |
| 1:20–1:40 | Open subscription imports and Sync Activity.                   | “Full mode previews OAuth or Takeout imports, deduplicates candidates, and runs commits as durable jobs. Every refresh records progress, safe errors and retry state.” |
| 1:40–1:55 | Show the architecture diagram and CI badge.                    | “Docker runs FastAPI, PostgreSQL, Redis and arq workers. The Vercel demo shares the same code and migrations but stays RSS-only to protect quota.”                     |
| 1:55–2:00 | Return to the demo URL.                                        | “The live demo and complete self-hosting instructions are linked from GitHub.”                                                                                         |

The release video uses these lines as burned captions. The same text is published as Markdown and
WebVTT so the walkthrough is understandable without audio.

## Longer interview walkthrough

### Product and data ownership

Start in Inbox and explain why the product stores a durable library rather than proxying YouTube on
every page load. Show categories, tags and Watch Later, then discuss `owner_id` scoping, cross-user 404
behavior, transactional account deletion and the current per-owner content duplication trade-off.

### Synchronization and quota

Open Sync Activity and a channel status. Explain RSS conditional requests, centralized Data API unit
accounting, batched metadata calls, active-run deduplication and the scheduler's all-channel pagination.
Use a historical failure to discuss safe error bodies, correlation IDs and bounded retries.

### Asynchronous execution

Trace a manual refresh from `202 SyncRunOut`, through Redis/arq, to PostgreSQL counters and terminal
state. Emphasize that the durable record—not the queue result—is the user-visible source of truth and
that using the run UUID as job ID makes duplicate delivery safe.

### Authentication and imports

Describe short access tokens plus rotating HTTP-only refresh sessions at the SvelteKit proxy. On the
import screen, explain one-use OAuth state, minimum Google scope, immediate token disposal, CSV row
validation and partial commit recovery.

### Deployment and resilience

Compare the Docker and Vercel diagrams. Docker is the full product with an hourly worker; Vercel is a
restricted daily-maintained showcase. Discuss migration-before-code ordering, Neon pooled versus direct
connections, last-good-data behavior, backup/restore and schema-compatible rollback.

### Accessibility and verification

Show keyboard navigation, visible focus and asynchronous announcements. Explain why axe is a CI gate
but not a conformance claim, and reference the recorded manual screen-reader, zoom and touch checklist.

## Recording checklist

- Use the canonical seeded state at 1920×1080 and 100% browser zoom.
- Hide bookmarks, notifications, personal browser data and developer tooling.
- Pause long enough for every caption to be read; keep pointer movement deliberate.
- Do not expose cookies, API keys, database URLs or Vercel/Neon dashboards.
- Undo watched and Watch Later changes after recording or invoke the authorized demo reset.
- Export H.264/AAC MP4 at 1080p, verify 90–120 seconds, then publish MP4, VTT and transcript together.
