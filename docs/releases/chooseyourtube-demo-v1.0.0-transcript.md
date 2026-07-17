# ChooseYourTube v1.0.0 video transcript

ChooseYourTube is a self-hostable YouTube inbox for intentional viewing—without recommendations,
comments or trending feeds.

Users follow only the channels they choose. PostgreSQL stores a durable personal library, so browsing
does not depend on a live YouTube request.

Search uses PostgreSQL full-text indexing, and URL-backed filters combine channel, tag, watched, date
and duration state.

Safe interactions remain owner-scoped. Watch Later is an application-owned system playlist with
ordered membership. The player preserves queue order and exposes failures instead of silently skipping
content.

Watch Later and custom playlists keep playback explicit and ordered. Playlists are durable, user-owned
collections rather than recommendation feeds.

Full mode previews OAuth or Takeout imports, deduplicates candidates, and runs commits as durable jobs.
Every refresh records progress, safe errors and retry state.

Docker runs FastAPI, PostgreSQL, Redis and arq workers. The Vercel demo shares the same code and
migrations but stays RSS-only to protect quota.

Try the live demo or follow the complete self-hosting guide at
`github.com/djdillybdev/ChooseYourTube`.
