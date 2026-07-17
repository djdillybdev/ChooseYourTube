# ChooseYourTube v1.0.0 video transcript

ChooseYourTube is a self-hosted YouTube inbox built for intentional viewing, without recommendations,
comments, or trending.

Users follow selected channels. PostgreSQL keeps a personal library, so browsing does not depend on a
live YouTube request.

Full-text search and URL-backed filters make larger subscription lists easier to browse and share.

User changes are owner-scoped. Watch Later is an ordered playlist stored by the application.

The player preserves queue order and reports playback failures instead of hiding them.

Full mode previews OAuth or Takeout imports, removes duplicates, and records progress and safe
failures for background work.

Docker runs FastAPI, PostgreSQL, Redis, and arq. The public demo uses the same code with daily RSS
maintenance.

The live demo and self-hosting guide are linked from the project README at
`github.com/djdillybdev/ChooseYourTube`.
