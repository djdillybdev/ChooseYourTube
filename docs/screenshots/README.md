# Portfolio screenshots

The checked-in portfolio set is captured from the deterministic hosted demo so the README shows the
same populated product a recruiter can open. Regenerate it from `frontend/` after a shipping UI or
seed change:

```sh
PORTFOLIO_BASE_URL=https://chooseyourtube-demo-tawny.vercel.app pnpm portfolio:screenshots
```

Without `PORTFOLIO_BASE_URL`, the command uses the deterministic fake backend for local capture. The
set covers demo entry, populated Inbox, filters, organization, Watch Later, import/sync evidence and
mobile navigation. It intentionally excludes recommendation, trending and engagement surfaces.

Capture only against the shared demo account. The workflow never reads credentials and its screenshot
path is read-only. Review every image for transient errors, missing thumbnails or personal browser data
before committing it.
