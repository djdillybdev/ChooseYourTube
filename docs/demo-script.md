# Portfolio demo and interview guide

Demo: <https://chooseyourtube-demo-tawny.vercel.app>

The shared account requires no credentials and resets daily. Imports, channel changes, and manual
refresh are disabled to protect shared data and YouTube quota.

## Two-minute walkthrough

| Time      | On screen                                                | Narration                                                                                                                      |
| --------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 0:00-0:10 | Open the demo and select **Try the demo**.               | "ChooseYourTube is a self-hosted YouTube inbox built for intentional viewing, without recommendations, comments, or trending." |
| 0:10-0:30 | Show the populated Inbox and change list and grid views. | "Users follow selected channels. PostgreSQL keeps a personal library, so browsing does not depend on a live YouTube request."  |
| 0:30-0:50 | Combine search, category, tag, and duration filters.     | "Full-text search and URL-backed filters make larger subscription lists easier to browse and share."                           |
| 0:50-1:05 | Mark a video watched and add it to Watch Later.          | "User changes are owner-scoped. Watch Later is an ordered playlist stored by the application."                                 |
| 1:05-1:20 | Start playback and show the queue.                       | "The player preserves queue order and reports playback failures instead of hiding them."                                       |
| 1:20-1:40 | Open subscription imports and Sync Activity.             | "Full mode previews OAuth or Takeout imports, removes duplicates, and records progress and safe failures for background work." |
| 1:40-1:55 | Show the architecture diagram and CI badge.              | "Docker runs FastAPI, PostgreSQL, Redis, and arq. The public demo uses the same code with daily RSS maintenance."              |
| 1:55-2:00 | Return to the demo URL.                                  | "The live demo and self-hosting guide are linked from the project README."                                                     |

The release video uses this narration as captions. Publish the Markdown transcript and WebVTT file
with the video so it remains understandable without audio.

## Longer technical walkthrough

### Product and data ownership

Start in Inbox and explain why the application stores a durable library instead of proxying YouTube
for every page. Show categories, tags, and Watch Later. Discuss `owner_id` scoping, cross-user 404
behavior, transactional account deletion, and the storage cost of per-owner content.

### Synchronization and quota

Open Sync Activity and a channel status. Explain RSS conditional requests, centralized Data API unit
accounting, batched metadata requests, active-run deduplication, and scheduler pagination. Use a stored
failure to show safe error messages, request IDs, and bounded retries.

### Background execution

Trace a manual refresh from the `202 SyncRunOut` response through Redis and arq to PostgreSQL counters
and terminal state. The PostgreSQL record is the user-visible source of truth. Using its UUID as the
job ID makes repeated delivery safe.

### Authentication and imports

Describe short-lived access tokens and rotating HTTP-only refresh sessions at the SvelteKit proxy.
Open the import screen and cover one-use OAuth state, minimum Google scope, immediate token disposal,
CSV validation, and partial import recovery.

### Deployment and recovery

Compare the Docker and Vercel diagrams. Docker includes an hourly worker. Vercel is a restricted
showcase with daily maintenance. Cover migration-before-code ordering, Neon pooled and direct
connections, last-good-data behavior, backup and restore, and schema-compatible rollback.

### Accessibility and verification

Show keyboard navigation, visible focus, and status announcements. Explain that axe is a CI check,
not a conformance claim. Point to the manual screen-reader, zoom, and physical-device checklist.

## Recording checklist

- Capture the canonical seeded state at 1920 by 1080 and 100% browser zoom.
- Hide bookmarks, notifications, personal browser data, and developer tools.
- Leave enough time to read each caption and keep pointer movement deliberate.
- Do not expose cookies, API keys, database URLs, or Vercel and Neon dashboards.
- Undo watched and Watch Later changes after recording, or run the authorized demo reset.
- Export an H.264 and AAC MP4 at 1080p. Check that it runs for 90 to 120 seconds, then publish the MP4,
  WebVTT captions, and transcript together.
