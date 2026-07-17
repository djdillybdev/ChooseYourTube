# Portfolio screenshots

The README screenshots use deterministic demo data so the repository and hosted demo show the same
product state. Regenerate the set after a visible interface or seed change.

From `frontend/`, capture the hosted demo:

```bash
PORTFOLIO_BASE_URL=https://chooseyourtube-demo-tawny.vercel.app pnpm portfolio:screenshots
```

Without `PORTFOLIO_BASE_URL`, the Playwright workflow uses the local deterministic fake backend. The
capture set includes demo entry, Inbox, filters, organization settings, Watch Later, import and
synchronization history, and mobile navigation.

Use only the shared demo account when capturing against the hosted application. The workflow does not
accept credentials. Before committing images, check each file for:

- transient API or thumbnail failures;
- missing or unexpected seeded content;
- personal browser data or notifications;
- inconsistent viewport size, zoom, or color theme;
- stale interface states that no longer match the README.

Do not add screenshots of recommendation, trending, comments, or engagement features; they are not
part of ChooseYourTube.
