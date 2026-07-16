# ChooseYourTube Frontend UX and Accessibility Implementation Plan

**Status:** Proposed implementation plan  
**Audit date:** 2026-07-16  
**Scope:** SvelteKit frontend, with narrowly scoped backend contract work where the frontend cannot
present an accurate state without it  
**Related plan:** `docs/portfolio-release-plan.md`, especially Phase 5 (accounts, UX, and
accessibility) and Phase 6 (tests)  
**Implementation authorization:** This document is planning only. Do not begin implementation
without the repository owner's approval.

## 1. Purpose and intended outcome

ChooseYourTube is a distraction-free YouTube client. It lets a user follow selected channels and
browse their videos without algorithmic recommendations, trending content, engagement feeds, or
other attention-maximizing UI. This plan converts the 2026-07-16 frontend audit into an incremental,
testable implementation sequence.

The work is complete when a new user can understand the product, sign in, follow a channel, see the
channel's synchronization state, find and play a video, and manage watched or saved state on a phone
or desktop without needing instructions. The same core tasks must be usable with keyboard and screen
reader input. Failure, loading, empty, and background synchronization states must be explicit and
actionable without exposing internal backend details.

This is not a redesign. The existing restrained visual language, route structure, typed API layer,
and SvelteKit architecture should remain. The work should make the current product clearer and more
robust rather than adding attention-grabbing features.

### 1.1 Product principles to preserve

- Keep video browsing quiet, content-led, and free of recommendations.
- Make following a known channel and finding its videos the shortest paths in the application.
- Prefer explicit state and plain language over unexplained icons or animation.
- Keep high-frequency actions visible without turning every card into a dense control panel.
- Use native HTML and progressive enhancement before custom interaction patterns.
- Preserve deep links and browser Back/Forward behavior for search, filters, sorting, and paging.
- Keep the scope credible for a personal portfolio project; reuse and consolidate before adding new
  systems.

### 1.2 Non-goals

- Trending, algorithmic recommendations, autoplay engagement loops, social activity, or an
  engagement feed.
- A wholesale visual redesign or migration away from SvelteKit, Tailwind, or DaisyUI.
- Replacing the current FastAPI/PostgreSQL/Redis worker architecture.
- Automatically marking a video watched merely because its card was opened. Preserve the current
  explicit watched control unless a separate product decision defines a reliable playback threshold.
- Building a new folder feature in this workstream. Existing folder code is addressed as an
  information-architecture decision, not expanded as a new feature.

## 2. Current application baseline

### 2.1 Route structure

The authenticated application is composed by `frontend/src/routes/+layout.svelte` and
`frontend/src/routes/+layout.ts`. The root layout loads bootstrap data, renders global navigation and
modals, and redirects unauthenticated users through the existing auth flow.

| User area | Routes | Current purpose |
| --- | --- | --- |
| Authentication | `/login`, `/register` | Password account entry and account creation |
| Main feed | `/inbox` | Recently synchronized videos; currently defaults to unwatched |
| Saved views | `/favorites`, `/watch-later` | Favorite videos and the Watch Later system list |
| Playlists | `/playlists`, `/playlists/[playlistId]` | Manual playlist browsing and playback |
| Channels | `/channels/[id]` | Channel videos and channel actions |
| Channel playlists | `/channels/[id]/playlists`, `/channels/[id]/playlists/[playlistId]` | Synced YouTube playlist browsing |
| Organization | `/categories/[id]`, `/folders/[id]` | Category and folder-scoped content |
| Playback | `/player` | YouTube embed and application queue |
| Settings | `/settings`, `/settings/account`, `/settings/sync`, `/settings/imports`, `/settings/imports/[id]` | Account, synchronization, and import management |
| Server endpoints | `/api/auth/*`, `/api/backend/[...path]`, `/api/bootstrap`, `/api/meta` | Same-origin auth, backend proxying, bootstrap, and runtime metadata |

### 2.2 Shared layout and navigation

- `frontend/src/routes/+layout.svelte` owns the skip link, main landmark, `Sidebar`, `TopBar`, global
  modal instances, route-loading live announcement, and Watch Later context.
- `frontend/src/lib/components/layout/Sidebar.svelte` contains the main destinations, categories,
  followed channels, desktop collapse behavior, and mobile drawer behavior.
- `frontend/src/lib/components/layout/TopBar.svelte` contains the watched-state selector, filters,
  current user email, and logout.
- `frontend/src/routes/settings/+layout.svelte` supplies settings navigation.
- Channel page headers are currently duplicated across channel video and playlist routes rather than
  represented by one shared component.

### 2.3 Major reusable components

| Area | Components |
| --- | --- |
| Video browsing | `VideoList.svelte`, `VideoCard.svelte`, `WatchLaterButton.svelte` |
| Channel browsing | `ChannelCard.svelte`, `ChannelContentTabs.svelte`, `ChannelFavoriteButton.svelte`, `SyncStatus.svelte` |
| Layout | `Sidebar.svelte`, `TopBar.svelte`, `CategoryTree.svelte`, `ChannelTreeItem.svelte`, `FolderTree.svelte`, `DemoBanner.svelte` |
| Player | `YouTubePlayer.svelte`, `QueueList.svelte` |
| Dialogs | `AddChannelModal.svelte`, create/edit category and folder modals, `EditChannelModal.svelte`, `SaveVideoModal.svelte`, `ConfirmDialog.svelte` |
| Common UI | `SearchBar.svelte`, `PaginationControls.svelte`, `EmptyState.svelte`, `ErrorState.svelte`, `SkeletonCard.svelte`, category icon controls |

### 2.4 Styling and design tokens

- Tailwind CSS 4 and DaisyUI provide layout and component utilities.
- `frontend/src/routes/layout.css` defines the Catppuccin-derived theme, application-level tokens,
  global focus-visible treatment, and reduced-motion rules.
- The current interface consistently uses a quiet base background, bordered cards, modest radii,
  and a single purple primary action. Those traits should remain.
- Page widths, channel headers, form fields, dialog structure, and status presentation are not yet
  consistently tokenized or shared.

### 2.5 State and data flow

- Page data is loaded through SvelteKit route loaders and typed API wrappers under
  `frontend/src/lib/api/`.
- Browser requests pass through `/api/backend/[...path]`; auth routes use HTTP-only access and
  refresh cookies.
- `frontend/src/lib/api/client.ts` centralizes API errors, retry/backoff, and session refresh.
- Search, filters, sorting, and pagination are represented in the URL and parsed by
  `frontend/src/lib/utils/videoFilterQuery.ts`. This is the correct source-of-truth pattern and
  should be retained.
- Cross-route client state uses Svelte stores for auth, modals, player/queue, Watch Later, sidebar
  UI, and category/folder expansion.
- `frontend/src/lib/stores/filterState.svelte.ts` is not the active filter source and should not be
  extended. Several persisted UI view properties are also unused and should be removed or explicitly
  adopted during consolidation.

### 2.6 Authentication and forms

- `frontend/src/hooks.server.ts` protects authenticated routes using access/refresh cookies.
- Login, register, logout, refresh, account, and demo auth are exposed as SvelteKit server routes
  under `frontend/src/routes/api/auth/`.
- Login and register pages currently use client-side `preventDefault` submission and `fetch` rather
  than SvelteKit form actions and `use:enhance`.
- Field and request errors are visually rendered but are not consistently associated with inputs or
  announced. Network rejection is not consistently handled.

### 2.7 Loading, error, and accessibility conventions

Existing strengths that must be preserved:

- A skip link and stable main landmark exist.
- Global `:focus-visible` styling and reduced-motion overrides exist.
- The mobile drawer makes obscured content inert, supports Escape, and restores focus.
- Most icon buttons have accessible names.
- Synchronization activity uses durable run state, polling, status regions, retryable failure
  handling, and quota information.
- Empty-state, pagination, confirm-dialog, and skeleton components already exist.

Current gaps:

- Route loading is announced to assistive technology but has almost no visible feedback.
- `SkeletonCard.svelte` is not used in the primary video-loading paths.
- Several routes discard useful error details and render generic, non-retryable error states.
- Mutation failures are sometimes logged only to the console.
- Dynamic success/failure status is not consistently announced.
- Global modal focus management is inconsistent even though `ConfirmDialog.svelte` demonstrates a
  working focus-restoration pattern.

### 2.8 Existing frontend tests

- Vitest, Testing Library, MSW, and jsdom cover server utilities and components.
- Playwright has a deterministic fake backend (`frontend/tests/e2e/fake-backend.mjs`) and a separate
  full-stack suite (`frontend/tests/e2e-full/full-stack.test.ts`).
- `@axe-core/playwright` is installed and used, but authenticated-page checks currently disable
  color contrast and generally scan only closed component states.

### 2.9 Run and verification commands

From the repository root:

```bash
cp .env.example .env
make up       # full stack on frontend 5173 / API 8000
make dev-up   # bind-mounted development stack on frontend 5174 / API 8001
make logs
make down
```

Frontend-only development and verification:

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
pnpm check
pnpm lint
pnpm test:unit
pnpm test:coverage
pnpm test:e2e:fast
pnpm test:e2e:full
pnpm test:e2e
```

When an API contract changes, run:

```bash
cd frontend
pnpm api:generate
pnpm api:check
```

### 2.10 Audit evidence and limitations

The 2026-07-16 audit inspected the repository and exercised the built application against the fake
backend at 320, 375, 768, 1280, and 1440 CSS-pixel widths. Login and logout completed. The supplied
screenshots also showed the channel page, Add Channel dialog, open filters, and desktop inbox.

Baseline results at audit time:

- `pnpm check`: passed with zero errors or warnings.
- `pnpm lint`: failed on one `svelte/prefer-writable-derived` error in
  `frontend/src/lib/components/channel/ChannelFavoriteButton.svelte`.
- `pnpm test:unit`: 43 files and 129 tests passed.
- `pnpm test:e2e:fast`: 10 tests passed.

Observed runtime evidence:

- At 320 px, the 320 px-wide filter dropdown began at approximately x = -193, leaving most controls
  off-screen.
- At 375 px, channel header actions overlapped the channel title and the video Play action was absent
  until pointer hover or descendant focus.
- At 768 px, the top bar's content was wider than its available center region and was visibly clipped.
- Axe on the open filter surface found critical missing-label failures for two date inputs, critical
  missing-name failures for four selects, and serious contrast failures.
- Opening Add Channel focused the import link instead of the primary channel input. Closing it left
  focus on `body` instead of returning focus to the Add Channel trigger.

The audit did not exercise a persistent full-stack database, live YouTube iframe behavior, real
YouTube API credentials, registration email delivery, worker/Redis outages, quota exhaustion, or
real deleted/private channels. VoiceOver/NVDA and forced-colors testing were not completed. These
limitations are represented as required validation rather than assumed passes.

## 3. Success criteria

The implementation should meet all of the following release-level outcomes:

1. A user can start playback from every video list with touch, mouse, or keyboard without revealing
   hover-only controls first.
2. All filter choices, including **All**, round-trip through the URL and backend request correctly.
3. Shorts are excluded from normal feeds by default, matching the product promise, while an explicit
   opt-in remains possible if retained.
4. No primary control is clipped, overlaps another control, or causes horizontal scrolling at 320,
   375, 768, 1280, or 1440 px, or at 200% browser zoom.
5. Every input, select, segmented state control, icon button, dialog, and dynamic status has an
   accessible name, state, and keyboard path.
6. Opening and closing every dialog uses a predictable initial focus target and restores focus to
   its trigger on Cancel, Escape, backdrop close where supported, success, and failure.
7. Following a channel distinguishes **followed**, **sync queued**, **sync running**, **videos
   available**, **partial**, and **failed** states.
8. Mutations never fail only in the browser console. The user receives a concise message and a retry
   or recovery action when one is safe.
9. The principal routes pass automated Axe scans, including open dialogs, filter surfaces, the
   mobile drawer, and queue controls, with color contrast enabled and no serious or critical
   violations.
10. The core login, follow-channel, browse, filter, play, watched, Watch Later, sync failure, and
    session-expiry flows have deterministic automated coverage plus a recorded manual accessibility
    pass.

## 4. Implementation decisions

These defaults make the plan executable without reopening basic design questions. If the product
owner chooses a different behavior, record the decision in this section before implementation so
tests and copy stay consistent.

### 4.1 Video cards

- The title and thumbnail area are the persistent primary playback action.
- Because playback first updates application queue state and then navigates to `/player`, use a
  native `button`, not a plain link pretending navigation is the only effect.
- Keep channel navigation as a separate native link.
- Keep Watch Later visible. Keep watched state visible as a compact toggle. Put lower-frequency
  **Save**, **Play next**, and **Add to queue** actions in a labelled overflow menu on narrow layouts
  or show them as secondary controls when space permits.
- Do not make the whole card one interactive element; that would nest Watch Later, channel, and menu
  controls inside another control.

### 4.2 Watched and Shorts URL state

Keep backend query names to minimize contract churn, but represent tri-state UI explicitly:

| UI state | URL | Backend filter |
| --- | --- | --- |
| All watched states | `is_watched=all` | omit `is_watched` |
| Unwatched | `is_watched=false` | `is_watched=false` |
| Watched | `is_watched=true` | `is_watched=true` |
| All lengths | `is_short=all` | omit `is_short` |
| Standard videos | `is_short=false` | `is_short=false` |
| Shorts only | `is_short=true` | `is_short=true` |

For `/inbox`, absence of `is_watched` remains the backward-compatible default of Unwatched. Selecting
**All** must write `is_watched=all`; deleting the parameter must not be used for All on this route.
For normal video lists, absence of `is_short` defaults to standard videos so Shorts are not shown by
default. Selecting **All lengths** writes `is_short=all`. `parseVideoFilterQuery` maps the literal
`all` to `undefined` in API filters while retaining an explicit UI state. Existing `true`/`false`
deep links remain valid.

`Clear all filters` resets to each route's documented defaults, not necessarily every-content state.
On Inbox that means Unwatched and standard videos. Copy should say **Reset filters** if that behavior
would otherwise be misleading.

### 4.3 Feedback model

- Prefer an inline message next to the task for persistent or recoverable errors.
- Use one restrained application status region for short-lived cross-route confirmations such as
  “Added to Watch Later.” Do not build a stacked, animated notification feed.
- `role="status"`/polite live regions are for success, progress, and non-urgent changes.
- `role="alert"` is for an error that blocks the current task. Avoid repeatedly announcing polling
  updates.
- Optimistic mutations must roll back on failure and keep the relevant control focused.
- Safe backend messages and request IDs may be displayed. Stack traces, provider payloads, internal
  queue names, and raw exception text must not be displayed.

### 4.4 Follow-channel and initial-sync contract

The frontend cannot truthfully distinguish “channel saved” from “initial sync queued” with the
current create response. Introduce a focused result contract:

```json
{
  "channel": { "id": "...", "title": "...", "handle": "..." },
  "initial_sync": {
    "id": "...",
    "status": "queued",
    "error_code": null,
    "error_message": null
  }
}
```

The backend returns `201 Created` once the channel record exists, even if enqueueing the first sync
produces a durable failed sync run. In that case `initial_sync.status` is `failed`, allowing the UI to
say that the channel was followed but videos could not yet be synchronized. A retry must not create a
duplicate channel. Invalid/unresolvable input fails before creation with a stable field-level error.

Accept only formats the backend actually resolves. Preferred supported inputs are `@handle` and
YouTube URLs containing `/@handle`. Support `/channel/UC...`, `/c/...`, or `/user/...` only after an
explicit resolver is implemented and tested; until then, narrow the form copy rather than promising
generic “channel URL” support.

### 4.5 Folders and organization terminology

Categories are the active visible organization mechanism. Folder routes, modal components, stores,
and `FolderTree.svelte` exist but the current sidebar does not expose a coherent folder flow. For the
portfolio UI, defer folders rather than presenting two unexplained channel-grouping models. Keep the
backend contract intact, remove or stop loading unreachable frontend folder affordances after
confirming no supported flow depends on them, and document folders as deferred. If folders are later
restored, they require a separate end-to-end organization plan.

Use these labels consistently:

- **Categories** for user-created channel groupings shown in navigation.
- **Tags** for cross-cutting video/channel metadata used by filters.
- **Playlists** for ordered video collections.
- **Watch Later** for the system-owned saved list.

### 4.6 Responsive and accessibility target

- Design from 320 CSS pixels upward; 375, 768, 1280, and 1440 are required regression widths.
- At 200% desktop zoom, content must reflow to an equivalent narrow layout without two-dimensional
  scrolling, except where a genuinely tabular region needs its own labelled scroll container.
- Interactive targets should be at least 24 by 24 CSS pixels under WCAG 2.2 AA and should target 44
  by 44 for primary touch actions where practical.
- No essential action may depend on hover. Hover may add emphasis but not capability.
- Use native elements first. Custom composite widgets require documented keyboard behavior and
  tests.

## 5. Finding register

The IDs below are used throughout the phases. “Objective” indicates directly observed or
standards-based problems; “Design judgment” indicates a recommended consistency improvement.

| ID | Severity | Type | Finding | Primary evidence |
| --- | --- | --- | --- | --- |
| F-01 | High | Objective | Playback and most video actions are hover/focus-revealed; title and thumbnail are inert | `VideoCard.svelte`, `VideoList.svelte`; touch-width runtime review |
| F-02 | High | Objective | Filter surface leaves the viewport at 320 px | `TopBar.svelte` fixed `w-80 dropdown-end`; measured runtime bounds |
| F-03 | High | Objective | Filter and search controls lack programmatic labels/state; contrast failures occur in the open state | `TopBar.svelte`, `SearchBar.svelte`; Axe open-state results |
| F-04 | High | Objective | Channel header and top bar overlap or clip at 375/768 px; header markup is duplicated | Channel route components and `TopBar.svelte`; runtime review |
| F-05 | High | Objective | Inbox All cannot be represented because removing `is_watched` reapplies the Unwatched default | `videoFilterQuery.ts`, `inbox/+page.ts`, `TopBar.svelte` |
| F-06 | High | Objective | Add Channel conflates record creation with initial sync and overpromises URL support | `AddChannelModal.svelte`; `backend/app/routers/channels.py`; channel service normalization |
| F-07 | High | Objective | Several mutations and page loads fail silently or without retry/recovery | `VideoCard.svelte`, player state, Inbox/Playlists routes, `+error.svelte` |
| F-08 | High | Objective | Global dialogs do not consistently set initial focus or restore the trigger | Global modal components versus `ConfirmDialog.svelte`; runtime focus review |
| F-09 | High | Objective | Nested/custom interactions and drag-only reordering create keyboard barriers | `ChannelCard.svelte`, `QueueList.svelte`, Watch Later/playlist reorder UI |
| F-10 | High | Objective/product mismatch | Shorts appear by default despite the product's stated “without Shorts” purpose | Filter defaults, Inbox screenshot, fake-backend runtime |
| F-11 | Medium | Objective | Active navigation, settings semantics, organization labels, and growing channel navigation are inconsistent | `Sidebar.svelte`, settings layout, dormant folder flow |
| F-12 | Medium | Objective | Auth forms require JavaScript and provide incomplete validation/error association | Login/register pages and auth server endpoints |
| F-13 | Low | Design judgment | Shared page widths, headers, fields, statuses, and card proportions are visually inconsistent | Route-level utility classes and duplicated markup |

## 6. Delivery strategy

### 6.1 Pull request rules

- Each pull request should solve one coherent behavior, include its tests, and leave all existing
  checks green.
- Follow frontend TDD: add a failing component/unit/e2e assertion for each regression before or with
  the implementation.
- Do not combine API response-contract changes with unrelated visual polish.
- Include before/after screenshots at 375 and 1280 px for visible UI changes. Include 320 or 768 px
  when that width is the regression target.
- Regenerate and verify OpenAPI types in the same pull request as any backend schema change.
- Preserve loaded data during background failures and avoid schema migrations unless the channel
  create contract proves one is necessary.

### 6.2 Required checks for every frontend pull request

```bash
cd frontend
pnpm api:check
pnpm check
pnpm lint
pnpm test:unit
pnpm test:e2e:fast
```

Use `pnpm test:coverage` for changes to shared components, stores, or API behavior. Use
`pnpm test:e2e:full` for auth/backend contract, synchronization, or ownership changes. Run the
relevant backend Ruff, mypy, and pytest suites when backend code changes.

### 6.3 Phase dependency summary

```text
Phase 1 core tasks
  ├── Video interaction foundation ──> Phase 2 keyboard semantics ──> Phase 6 shared cards
  └── URL/filter correctness ────────> Phase 2 accessible filters ─> Phase 5 responsive checks

Phase 2 accessible primitives ──────> Phase 3 auth/navigation and all later dialog work
Phase 3 route/form semantics ───────> Phase 4 session/error handling
Phase 4 status contracts ───────────> Phase 6 component consolidation
Phases 1–6 ─────────────────────────> Phase 7 visual polish and release audit
```

## 7. Phase 1 — Core-task blockers

**Goal:** Make primary video browsing and filtering function correctly on every input mode before
broader cleanup.

**Findings:** F-01, F-02, F-05, F-10  
**Estimated scope:** Medium, split into two focused pull requests

### PR 1.1 — Persistent, responsive video playback action

Tasks:

1. Refactor `VideoCard.svelte` so its thumbnail/title playback action is always rendered as a native
   button and invokes the existing queue-aware `handlePlay` path.
2. Render the channel title as a separate link to `/channels/[id]` when channel metadata is available.
3. Keep Watch Later and watched-state controls permanently operable. Place lower-frequency actions
   behind a labelled menu at narrow widths if showing all controls causes crowding.
4. Remove the misleading pointer cursor from non-interactive card space and the state model that
   controls action existence through `isHovered`. Hover/focus styling may remain presentational.
5. Use an exact `aspect-video` thumbnail container, responsive width, and a compact stacked layout on
   the smallest width. Preserve duration, watched, and Short badges without overlay collisions.
6. Make failed playback, queue insertion, watched updates, and save actions visibly recoverable. A
   minimal inline status can be introduced here and consolidated in Phase 4.

Likely files:

- `frontend/src/lib/components/video/VideoCard.svelte`
- `frontend/src/lib/components/video/VideoList.svelte`
- `frontend/src/lib/components/video/WatchLaterButton.svelte`
- `frontend/src/lib/stores/playerState.svelte.ts`
- `frontend/src/lib/services/queuePlaylist.ts`
- Component and Playwright tests under `frontend/tests/`

Acceptance criteria:

- Play is visible and operable with touch at 320/375 px before any hover or focus event.
- Tab reaches playback, channel, Watch Later, watched state, and overflow actions in logical order.
- No nested interactive element Axe violation exists.
- A failed `onPlay`, queue request, watched update, or save does not navigate and produces visible,
  announced feedback.
- Long titles remain readable to two lines and do not push actions out of the card.

### PR 1.2 — Correct filter semantics and minimum viewport containment

Tasks:

1. Extend `videoFilterQuery.ts` with the explicit `all` behavior defined in Section 4.2.
2. Update `TopBar.svelte` query-writing logic so Inbox All writes `is_watched=all` and can be restored
   through Back/Forward or a copied URL.
3. Default normal video lists to `is_short=false`, while preserving an explicit All lengths option.
4. Decide route defaults in one exported configuration rather than repeating path checks in loaders
   and `TopBar`.
5. Prevent the existing filter surface from leaving the viewport at 320 px. A full accessible
   extraction occurs in Phase 2, but this PR must leave no unreachable control.
6. Rename **Clear all filters** to **Reset filters** where the result returns to route defaults.

Likely files:

- `frontend/src/lib/utils/videoFilterQuery.ts`
- `frontend/src/lib/components/layout/TopBar.svelte`
- Video-list `+page.ts` loaders, especially `frontend/src/routes/inbox/+page.ts`
- Existing/new filter utility tests and Playwright inbox tests

Acceptance criteria:

- Inbox All returns watched and unwatched fixture videos and preserves `is_watched=all` in the URL.
- Inbox Unwatched and Watched produce the correct API query and active state.
- Standard videos are the initial result set; Shorts appear only after an explicit opt-in.
- Refresh and browser Back/Forward preserve the selected state.
- Every filter control is visible at 320 px without horizontal document or internal top-bar overflow.

### Phase 1 exit gate

- Touch, keyboard, and mouse users can open a video from each principal list.
- All watched/length states have deterministic URL and API behavior.
- New component/unit tests cover the tri-state parser and persistent playback control.
- Playwright covers 320 and 375 px regressions.

## 8. Phase 2 — Keyboard and screen-reader blockers

**Goal:** Establish accessible shared interaction primitives before changing more forms and pages.

**Findings:** F-03, F-08, F-09 and the accessibility portions of F-01/F-02  
**Estimated scope:** Medium to Large, split into three pull requests

### PR 2.1 — Accessible video filters and search

Tasks:

1. Extract the video filtering UI from `TopBar.svelte` into a focused `VideoFilters.svelte`.
2. Use a fieldset and legend for the All/Unwatched/Watched choice. Native radios styled as a
   segmented control are preferred. If buttons are retained, expose `aria-pressed` and a clear group
   name.
3. Give every select and date input an actual `<label for>` and stable unique ID. Keep visual helper
   text linked with `aria-describedby` when needed.
4. Give `SearchBar.svelte` a programmatic label. A route-specific visible label may be visually
   hidden if the placeholder already provides sufficient sighted context; the placeholder must not
   be the accessible name.
5. On desktop, use a keyboard-operable popover/details surface that remains within the viewport. On
   mobile, use the shared dialog primitive from PR 2.2 or a full-width in-flow disclosure. Do not
   implement an untested custom menu role for a form.
6. Keep focus stable after a filter navigation (`keepFocus`) and announce the new result count once
   loading completes.
7. Adjust theme/control tokens until default, hover, focus, disabled, selected, placeholder, and date
   control contrast pass with Axe contrast checks enabled.

Likely files:

- `frontend/src/lib/components/layout/TopBar.svelte`
- New `frontend/src/lib/components/video/VideoFilters.svelte`
- `frontend/src/lib/components/ui/SearchBar.svelte`
- `frontend/src/routes/layout.css`
- Filter component and e2e accessibility tests

Acceptance criteria:

- Axe reports no serious/critical issue with the filter surface open.
- A screen reader announces every field's label, current value, and segmented selection.
- Escape closes the mobile filter dialog and restores the Filters trigger if a dialog is used.
- Applying, resetting, and navigating filter history does not lose focus or scroll unexpectedly.

### PR 2.2 — Shared dialog focus contract

Create a small `DialogShell.svelte` (or an equivalent action/helper) based on the working behavior in
`ConfirmDialog.svelte`.

Required contract:

- The trigger element is captured before `showModal()`.
- `aria-labelledby` points to a unique visible title; optional description uses `aria-describedby`.
- Initial focus is explicit per dialog: primary input for creation/edit forms, least destructive
  action for destructive confirmation, and first meaningful choice for selection dialogs.
- Tab remains within the native modal dialog.
- Escape and Cancel close when no blocking request is in flight.
- Backdrop behavior is consistent and cannot discard an in-flight destructive action.
- Every close path restores the original trigger if it still exists; otherwise focus moves to the
  nearest stable page heading or main landmark.
- Busy submissions expose `aria-busy`, disable duplicate submission, and retain readable button
  text.

Migrate:

- `AddChannelModal.svelte`
- `CreateCategoryModal.svelte` and edit category dialog
- Folder modals while they remain mounted; remove them later if folders are deferred
- `EditChannelModal.svelte`
- `SaveVideoModal.svelte`
- `ConfirmDialog.svelte` itself, avoiding a second behavior implementation

Acceptance criteria:

- Automated tests cover open, initial focus, Tab/Shift+Tab, Escape, Cancel, submit success, submit
  failure, and trigger removal fallback.
- Add Channel initially focuses the handle field, not the import link.
- No close path leaves focus on `body`.

### PR 2.3 — Native interactive semantics and keyboard reordering

Tasks:

1. Refactor `ChannelCard.svelte` so the channel link and favorite/edit/refresh buttons are siblings,
   not buttons nested inside an anchor.
2. Replace the clickable `div role="button"` in `QueueList.svelte` with native controls and separate
   the row-selection action from Remove.
3. Add explicit **Move up** and **Move down** buttons to ordered queue, Watch Later, and editable
   playlist rows. Drag-and-drop may remain as a pointer enhancement, never the only path.
4. Disable impossible moves at the first/last position. After a move, retain focus and announce the
   new position, for example “Moved Video title to position 2 of 6.”
5. Verify Space and Enter activation, logical source order, touch targets, and visible focus in every
   modified control.

Likely files:

- `frontend/src/lib/components/channel/ChannelCard.svelte`
- `frontend/src/lib/components/player/QueueList.svelte`
- Watch Later and playlist route components
- Relevant playlist/queue stores or API wrappers

### Phase 2 exit gate

- All dialogs follow one tested focus contract.
- Filters, search, channel cards, queue selection, removal, and reordering are keyboard complete.
- Authenticated Axe scans include open filters and dialogs with contrast enabled.
- The manual keyboard pass can complete filter, play, save, queue, and dialog flows without a
  pointer.

## 9. Phase 3 — Authentication, forms, and navigation

**Goal:** Make entry, session, and wayfinding behavior understandable and progressively enhanced.

**Findings:** F-11, F-12  
**Estimated scope:** Medium, split into two pull requests

### PR 3.1 — Progressive auth forms and session recovery

Tasks:

1. Implement SvelteKit server actions for login and registration while retaining the existing
   same-origin auth endpoints and secure cookie behavior.
2. Use `use:enhance` for pending state and smooth in-place validation, but ensure the forms complete
   correctly with JavaScript disabled.
3. Associate field errors through `aria-invalid` and `aria-describedby`; render a form error summary
   for request-level failures and move focus to it after a failed submit.
4. Catch network rejection and map stable API error codes to plain language. Do not show raw enum or
   backend exception strings.
5. Disable duplicate submission, keep entered email on recoverable failure, and never repopulate a
   password.
6. Preserve and validate `next` so forced authentication returns the user to a safe same-origin
   route. Reject open redirects.
7. Define session-expiration behavior: show “Your session expired. Sign in to continue,” preserve a
   safe return URL, and clear invalid cookies consistently.
8. Keep demo-login behavior mode-sensitive and covered separately from password auth.

Likely files:

- `frontend/src/routes/login/+page.svelte` and `+page.ts`/new `+page.server.ts`
- `frontend/src/routes/register/+page.svelte` and server action
- `frontend/src/routes/api/auth/*`
- `frontend/src/lib/api/auth.ts`, `frontend/src/lib/server/auth.ts`
- Auth unit, Playwright fake-backend, and full-stack tests

Acceptance criteria:

- Login and registration work with and without JavaScript.
- Invalid credentials, duplicate email, password validation, network failure, server failure, and
  expired session have distinct, announced, safe messages.
- Logout clears the authenticated UI and Back does not reveal protected cached content.

### PR 3.2 — Navigation state and information architecture

Tasks:

1. Add a consistent active state and `aria-current="page"` to Inbox, Favorites, Playlists, Watch
   Later, Settings, categories, and channels.
2. Treat settings destinations as navigation links, not ARIA tabs. Remove `role="tab"` unless a true
   in-page tab implementation with `aria-selected`, tablist ownership, and arrow-key behavior is
   intentionally built.
3. Ensure every page has one clear `h1`, a meaningful document title, and a stable return path to
   Inbox.
4. Preserve channel-to-video and playlist-to-player return URLs through playback.
5. Defer the incomplete folder UI as specified in Section 4.5: stop mounting unreachable folder
   modals/data in the root layout and remove unused client code only after reference and route tests
   prove it is not part of a supported flow. Keep backend data/routes intact.
6. Normalize Categories, Tags, Playlists, and Watch Later copy across Sidebar, filters, settings, and
   dialogs.
7. Add a lightweight channel find control when followed-channel count is large. Prefer filtering the
   existing sidebar list or a simple “All channels” list; do not add recommendation/search discovery.

Likely files:

- `frontend/src/lib/components/layout/Sidebar.svelte`
- `frontend/src/routes/settings/+layout.svelte`
- `frontend/src/routes/+layout.svelte` and `+layout.ts`
- Channel/category navigation components and page `<svelte:head>` blocks
- Folder components/stores only after confirmed deferral

### Phase 3 exit gate

- Account entry and session expiry are complete without JavaScript and understandable with a screen
  reader.
- Active navigation is announced and visible on every primary destination.
- Settings uses correct navigation semantics.
- No visible or mounted control advertises an incomplete organization flow.

## 10. Phase 4 — Loading, synchronization, error, and empty states

**Goal:** Make application state truthful and every recoverable failure actionable.

**Findings:** F-06, F-07 and state-feedback aspects of F-03/F-12  
**Estimated scope:** Large, split so the backend contract lands independently

### PR 4.1 — Follow-channel response and initial-sync lifecycle

Backend tasks:

1. Add a response schema equivalent to `ChannelCreateResult` containing `channel` and
   `initial_sync` summaries.
2. Refactor channel creation/enqueue orchestration so a committed channel plus failed enqueue is not
   reported as if nothing was created. Return the channel and durable failed run.
3. Make duplicate retry idempotent or return a stable `CHANNEL_ALREADY_FOLLOWED` error that includes
   the existing channel identifier where safe.
4. Make supported handle/URL formats explicit in validation. Add resolver support only with direct
   tests for each advertised form.
5. Preserve owner isolation and never expose provider payloads or infrastructure errors.
6. Regenerate `frontend/openapi.json` and `frontend/src/lib/types/generated.ts`.

Frontend tasks:

1. Turn Add Channel into an explicit sequence: input → submitting → followed/sync queued → optional
   progress → terminal success/partial/failure.
2. On queued/running result, close only if a visible page-level status persists; otherwise keep a
   concise result state in the dialog with **View channel** and **Done**.
3. On failed initial sync, say “Channel followed, but videos could not be synchronized” and provide
   **Retry sync** and **View channel** where permitted.
4. Show field-specific validation for unsupported URLs, invalid handles, private/deleted channels,
   and duplicates. Explain quota/worker unavailability in user terms.
5. Invalidate bootstrap/channel data once after confirmed creation; do not rely on a blind invalidation
   as success feedback.

Likely files:

- `backend/app/routers/channels.py`
- Channel orchestration/service and schema files under `backend/app/`
- `frontend/src/lib/api/channels.ts`
- `frontend/src/lib/components/modals/AddChannelModal.svelte`
- `frontend/src/lib/components/channel/SyncStatus.svelte`
- Generated API files, fake backend, MSW handlers, backend and frontend tests

Acceptance criteria:

- Tests distinguish invalid input, already followed, followed+queued, followed+failed enqueue,
  running, partial, succeeded, private/deleted, and quota failure.
- Retrying after enqueue failure never creates a duplicate channel.
- A user can always tell whether the channel exists and whether videos are ready.

### PR 4.2 — Shared action-status and API error presentation

Tasks:

1. Create a small typed UI result model for pending/success/error with optional safe retry. Keep API
   errors in `APIError`; do not duplicate transport logic in components.
2. Add one global polite status host for transient mutation confirmations and route-scoped inline
   `role="alert"` errors for blocking failures.
3. Update watched, favorite, Watch Later, save-to-playlist, queue, refresh, and reorder mutations to
   show pending state, prevent duplicates, roll back optimistic state, and report failure.
4. If playback/queue setup fails, remain on the current page and expose a retry.
5. Ensure status copy includes the affected object where useful, but remains concise.
6. Clear stale success messages on subsequent actions without moving focus.

Likely files:

- New shared status component/store under `frontend/src/lib/components/ui/` and/or
  `frontend/src/lib/stores/`
- `frontend/src/lib/api/client.ts`
- Video, channel, playlist, queue, and modal components
- Root layout status host

### PR 4.3 — Route loading, page errors, empty and partial states

Tasks:

1. Use visible skeletons or a restrained route progress indicator for initial data loads. Do not
   replace already loaded content with skeletons during background refresh.
2. Update `ErrorState.svelte` to accept heading, safe message, retry callback/link, and optional
   request ID. Use it consistently in Inbox, Playlists, channel pages, settings, and imports.
3. Update `frontend/src/routes/+error.svelte` to use safe `page.error.message` and status-specific
   next actions. Remove the unconditional “Your data was not changed” claim.
4. Preserve successfully loaded content with a non-blocking warning when a secondary or refresh
   request fails.
5. Define distinct empty states for no followed channels, no synchronized videos yet, no videos
   matching filters, empty playlist, empty Watch Later, and channel with no public videos.
6. Make authentication expiration route through the Phase 3 recovery flow.
7. Use bounded retry and explain when retry is not useful, such as quota exhaustion before reset.

Acceptance criteria:

- Every primary route has deterministic initial loading, empty, filtered-empty, failure, and retry
  coverage.
- Background sync failure never clears the last successful video list.
- Status changes are announced once and polling does not flood the live region.

### Phase 4 exit gate

- Follow-channel state is truthful across the API/UI boundary.
- No known primary mutation fails only in console output.
- All main route loaders offer an appropriate next action and preserve safe data.
- Fake-backend tests cover worker unavailable, quota, network, 401, 404, 409, 422, and 5xx cases.

## 11. Phase 5 — Mobile and responsive architecture

**Goal:** Remove remaining layout collisions and make each primary flow usable at narrow widths and
zoom after its behavior is stable.

**Findings:** F-02, F-04 and responsive aspects of F-01/F-13  
**Estimated scope:** Medium

### PR 5.1 — Shared responsive channel header

Tasks:

1. Extract duplicated channel heading markup into `ChannelHeader.svelte` with slots/props for avatar,
   title, handle, counts, sync status, favorite, edit, and refresh.
2. Use a small-screen grid or stacked flex layout: identity first, metadata/status second, actions in
   a wrapping row. Do not keep the 96 px avatar plus title plus actions in one non-wrapping line.
3. Shorten or icon-label secondary actions only when the accessible name remains complete. Keep
   Refresh state visible.
4. Handle long titles, handles, translated button text, missing avatars, and every sync-status length.
5. Use the component on channel videos, channel playlists, and channel playlist detail routes.

### PR 5.2 — Top bar, account controls, and page reflow

Tasks:

1. At mobile widths, give the navigation trigger, filter trigger, and account/logout actions defined
   non-overlapping regions.
2. Hide the full email behind a labelled account menu or allow safe truncation with an accessible
   full name. Do not let it consume the filter region.
3. Ensure desktop sidebar collapse, mobile drawer, filter surface, and route heading work together at
   200% zoom.
4. Normalize responsive content padding and maximum widths. Video lists should use available width
   without creating large empty card interiors on wide screens.
5. Test dialogs at 320 px and in constrained height: content scrolls inside the dialog, header/title
   remains available, and actions stay reachable without being permanently sticky over fields.
6. Verify the player/embed uses a responsive aspect ratio and queue controls remain reachable in
   constrained width and height.

Required fixture cases:

- 80-character channel and video titles.
- Long email address and category name.
- Missing thumbnail/avatar.
- Status text for queued, running, partial, failed, and succeeded.
- One video, hundreds of videos, and zero results.
- Browser text enlargement and 200% zoom.

### Phase 5 exit gate

- No control overlap, clipping, or unlabelled horizontal scrolling at 320, 375, 768, 1280, and 1440
  px.
- Core flows pass a real 200% browser zoom check, not only viewport emulation.
- Touch actions remain reachable and at least 24 by 24 CSS pixels, with 44 px targets for primary
  actions where practical.

## 12. Phase 6 — Component and visual-system consistency

**Goal:** Consolidate patterns proven in earlier phases so future pages inherit the fixes.

**Findings:** F-04, F-13 and implementation duplication discovered during prior phases  
**Estimated scope:** Medium

### PR 6.1 — Shared structural components

Consolidate only patterns that now appear at least twice:

- `PageHeader.svelte` for page title, count/description, and wrapping actions.
- `ChannelHeader.svelte` from Phase 5.
- `FormField.svelte` or a documented field pattern for label, description, input slot, and errors.
- `DialogShell.svelte` from Phase 2.
- `StatusBadge.svelte` for human-readable sync states.
- Enhanced `ErrorState.svelte`, `EmptyState.svelte`, and `SkeletonCard.svelte` from Phase 4.
- `VideoFilters.svelte` from Phase 2.

Keep components shallow and presentation-focused. Route loaders should continue data access; shared UI
must not start fetching arbitrary route data. Avoid a generic “everything card” component.

### PR 6.2 — Tokens and state inventory

Tasks:

1. Define a small set of content-width, spacing, radius, border, focus, status, and muted-text tokens
   in `layout.css`/theme configuration.
2. Replace direct low-contrast opacity combinations where they caused audit failures.
3. Document button hierarchy: primary for the page's main action, neutral for standard actions,
   ghost for low-emphasis actions, and explicit destructive styling.
4. Document form control states: default, hover, focus, invalid, disabled, pending, and read-only.
5. Render statuses as human language (“Sync queued,” “Last synced 21 minutes ago”), not raw lowercase
   enum values.
6. Remove unused `filterState.svelte.ts` and unused persisted UI view properties only after `rg` and
   tests confirm there are no consumers.
7. Fix the existing `ChannelFavoriteButton.svelte` writable-derived lint failure as part of the
   closest behavior/component PR, not as a formatting-only mass change.

### Phase 6 exit gate

- Equivalent actions use equivalent components and states across routes.
- Route pages no longer duplicate channel headers or field/dialog mechanics.
- `pnpm lint` is green, including the pre-existing writable-derived issue.
- New components have focused behavior tests and accessibility assertions.

## 13. Phase 7 — Visual polish and portfolio/demo release gate

**Goal:** Apply restrained final polish only after task behavior, accessibility, and responsive layout
are stable.

**Findings:** Remaining F-13 items and release-quality validation  
**Estimated scope:** Small to Medium

Tasks:

1. Tune typography hierarchy so each page has one dominant heading, secondary metadata is readable,
   and card titles remain the primary scan target.
2. Normalize card borders, hover/focus emphasis, spacing, radii, thumbnail aspect ratio, badge size,
   and button alignment through the Phase 6 tokens.
3. Reduce unused horizontal space on wide video lists without switching to a recommendation-like
   masonry or dense thumbnail grid. A readable centered list or modest two-column layout is
   acceptable only if scan order remains clear.
4. Verify disabled and loading states remain legible; avoid reducing opacity to the point of contrast
   failure.
5. Add or update portfolio screenshots showing login/demo entry, Inbox, channel page, filter state,
   follow-channel sync feedback, Watch Later, and mobile navigation. Use seeded data without secrets
   or personal email addresses.
6. Update `docs/accessibility.md` with the manual audit date, browser/assistive technology, known
   limitations, and linked fixes.
7. Run the complete release checklist in `docs/wcag-manual-checklist.md` and record evidence.

### Phase 7 exit gate

- Visual changes improve hierarchy or consistency and do not add content clutter.
- Screenshots match the shipping UI at required widths.
- Automated and manual release gates below pass, or a documented limitation has an owner and follow-up
  issue.

## 14. Detailed test plan

### 14.1 Component and unit tests

Add focused Testing Library/Vitest tests for:

#### `VideoCard.svelte`

- Play is present without hover and calls the queue-aware callback once.
- Failed play stays on the list and announces an error.
- Channel link is separate from playback and secondary controls.
- Watched and Watch Later optimistic state rolls back after mocked failure.
- Overflow actions are named and keyboard operable.
- Long/missing metadata does not remove the primary action.

#### `VideoFilters.svelte` and `videoFilterQuery.ts`

- Parse and serialize `true`, `false`, `all`, absent, invalid, and legacy values.
- Inbox absent watched value defaults to Unwatched; explicit All remains All.
- Absent length defaults to standard; explicit All omits the API filter.
- Date bounds use start/end of day and invalid dates are ignored safely.
- Reset returns route defaults and resets page to 1.
- Every field is reachable by its accessible label.

#### `DialogShell.svelte`

- Captures trigger and uses configured initial focus.
- Escape, Cancel, backdrop, submit success, and submit failure behave as specified.
- Busy state blocks duplicate submit and inappropriate close.
- Focus restores to trigger or stable fallback.
- Title and description relationships are present.

#### `ChannelHeader.svelte`

- All status variants and optional actions render human-readable text.
- Missing avatar and long identity text preserve accessible names.
- Only supported actions enter the tab order.

#### Status, error, and reorder components

- `ErrorState` exposes retry only when provided and includes safe request ID text.
- Polite and assertive messages use the correct live-region semantics.
- Reorder controls disable invalid moves, retain focus, and announce the resulting position.
- Status badges do not convey state by color alone.

### 14.2 Playwright user-flow tests

Use deterministic fake-backend fixtures for fast tests and the seeded full stack for contract/ownership
tests.

1. **Register, login, logout:** submit with validation errors, register, land on Inbox, logout, verify
   protected Back navigation does not reveal data.
2. **Session expiry:** expire access and refresh sessions during a safe route; verify one refresh
   attempt, then clear session and return to login with a validated `next` URL.
3. **Follow channel success:** enter supported handle, receive queued run, open channel, poll running
   then succeeded, and see videos without a full reload.
4. **Follow channel partial/failure:** simulate invalid handle, duplicate, private/deleted, queue
   unavailable, quota exhausted, and initial-sync partial. Verify exact recovery actions.
5. **Inbox filters:** assert All/Unwatched/Watched UI, URL, API request, and result fixtures. Repeat for
   standard/All lengths/Shorts only, channel, tag, date, sort, pagination, Back, and Forward.
6. **Touch playback:** at 320 and 375 px, tap title/thumbnail without hover, open player, use return
   action, and retain filters/scroll where supported.
7. **Watched and Watch Later:** update optimistically, simulate success and failure rollback, then
   verify destination lists.
8. **Queue/save:** add next/end, save to a custom playlist, simulate API failure, and verify a visible
   retry rather than console-only failure.
9. **Keyboard reorder:** move an item down/up in queue, Watch Later, and editable playlist; verify
   focus and announcement.
10. **Route states:** initial loading, no channels, sync pending/no videos, filtered empty, route
    failure, background refresh failure with stale content, retry success, and 404.
11. **Navigation:** active state and `aria-current` across Inbox, Favorites, Playlists, Watch Later,
    Settings, category, and channel routes.
12. **Player failure:** blocked/failed embed or queue item produces an assertive status and controlled
    skip behavior without trapping focus.

### 14.3 Automated accessibility scans

Run Axe with color contrast enabled against:

- Login and register, including validation errors.
- Inbox default and open filter states.
- Add Channel open in initial, validation, queued, and failure states.
- Mobile navigation drawer open.
- Channel page and channel action/menu states.
- Playlist and Watch Later with reorder controls.
- Player with queue and a simulated embed error.
- Settings account, synchronization, imports, and import detail.
- Confirmation and save dialogs open.

CI must have no serious or critical violations. Do not disable an Axe rule globally to ship a known
failure. If a third-party YouTube iframe produces an external violation, scope and document that
exception precisely while testing the application's iframe title and surrounding controls.

### 14.4 Responsive checks

For each principal route at 320, 375, 768, 1280, and 1440 px:

- Assert `document.documentElement.scrollWidth <= clientWidth` unless the test targets a documented
  local scroll region.
- Assert filter/dialog bounding boxes remain inside the viewport.
- Assert channel title, status, and action boxes do not intersect.
- Assert primary playback and Add Channel actions are visible and have non-zero touch targets.
- Use long strings, missing images, maximum action sets, and each status variant.
- Separately perform real browser 200% zoom and text-only enlargement checks; viewport emulation is
  not an adequate substitute.

### 14.5 Failure-state contract tests

Mock at least:

- Offline/network rejection.
- 401 with successful refresh and 401 with failed refresh.
- 403 demo-mode feature restriction.
- 404 missing/deleted channel or playlist.
- 409 duplicate channel or conflicting reorder.
- 422 invalid handle/date/form input.
- 429/provider quota exhausted.
- 500 application error with request ID.
- 503 worker/Redis unavailable.
- Queued → running → succeeded, partial, failed, timeout, and retry transitions.

Assert that raw backend details never appear and that the safe next action matches retryability.

### 14.6 Manual accessibility and media checks

Record tester, date, browser, operating system, assistive technology, viewport, failures, and linked
fixes.

- Keyboard-only: complete login, navigation, follow channel, filter, play, Watch Later, save, reorder,
  refresh, and logout.
- VoiceOver with Safari on macOS, and NVDA with Firefox or Chrome on Windows when available: verify
  headings, landmarks, control names/states, result counts, sync announcements, errors, and dialogs.
- Reduced motion: confirm route, hover, loading, and dialog behavior does not rely on animation.
- Forced colors/high contrast: verify focus, selected, watched, error, success, and disabled states.
- 200% zoom and 320 CSS px: confirm reflow and target reachability.
- Real YouTube iframe: verify accessible name, keyboard reachability, captions/fullscreen controls,
  blocked embed behavior, and end-of-queue behavior. Do not claim the third-party player's internal
  accessibility without this check.

## 15. API and data-contract notes

Most work is frontend-only. The follow-channel response is the deliberate exception because the
current API can commit a channel and then report a queue failure as an undifferentiated failed create.

Rules for that contract change:

- Prefer an additive schema and clear response type over frontend inference from follow-up list calls.
- Return stable `code`, safe `message`, `retryable`, and `request_id` through the repository's shared
  API error shape.
- Preserve durable sync-run status as the source of truth; do not invent a frontend-only “syncing”
  timer.
- Treat a committed channel as success even if its initial sync run failed, then present the partial
  outcome honestly.
- Update backend router/service tests, OpenAPI, generated TypeScript, MSW handlers, fake backend, and
  full-stack tests in the same pull request.
- No database migration is expected if the existing durable sync-run model contains all necessary
  fields. If it does not, document the migration and rollback in PR 4.1 rather than storing status in
  an unstructured channel field.

## 16. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Filter URL changes break old links | Continue accepting existing `true`/`false` and absent values; add explicit `all` rather than renaming backend parameters |
| Video card becomes visually busy | Keep only play, Watch Later, and watched state persistent; group low-frequency actions in a labelled menu |
| Shared components become over-general | Extract only repeated, stable patterns after behavior phases; keep data loading in routes |
| Live regions become noisy during polling | Announce lifecycle transitions and user-triggered results, not every poll |
| Dialog refactor causes focus regressions | Build one primitive with component tests before migrating each modal |
| Channel create API change introduces partial-commit ambiguity | Make committed channel plus durable sync outcome one explicit success response; test retry idempotency |
| Shorts default surprises existing users | Preserve an explicit All lengths/Shorts option, document the product-aligned default, and retain old deep-link parsing |
| Removing folder UI hides user data | Keep backend routes/data, verify no supported navigation before frontend cleanup, and treat restoration as separate scope |
| DaisyUI theme updates reintroduce contrast issues | Test open/disabled/selected states with contrast enabled and centralize adjusted tokens |
| Fake backend masks integration behavior | Pair API/auth/sync contract PRs with the full-stack suite and targeted manual failure injection |

## 17. Definition of done for every phase

- All phase acceptance criteria are met and linked in the pull request.
- Behavior tests fail before the fix or otherwise demonstrate the prior regression.
- Svelte/TypeScript check, lint, relevant unit/component tests, and fast Playwright tests pass.
- API schema drift and full-stack tests pass when contracts change.
- Keyboard and responsive checks are recorded for touched flows.
- Axe is run with the changed surface open, not only at default page load.
- User-visible copy is plain, safe, and consistent with product terminology.
- No essential action is hover-only, color-only, drag-only, or dependent on JavaScript when a normal
  form submission can work.
- Screenshots accompany visible changes at appropriate widths.
- Documentation is updated when behavior, supported input formats, URL state, or known accessibility
  limitations change.

## 18. Highest-value implementation candidates

These are the first five candidates to schedule if work must be selected independently.

### 1. Persistent responsive video playback

- **User benefit:** Every user, especially touch and keyboard users, can perform the product's primary
  task immediately.
- **Scope:** Medium.
- **Main files:** `VideoCard.svelte`, `VideoList.svelte`, player/queue state, related tests.
- **Dependencies:** None. It establishes patterns used by later interaction cleanup.

### 2. Correct, responsive, accessible filter system

- **User benefit:** Users can trust All/Unwatched/Watched and Shorts behavior and can reach every
  filter at mobile width or with assistive technology.
- **Scope:** Medium.
- **Main files:** `TopBar.svelte`, new `VideoFilters.svelte`, `videoFilterQuery.ts`, `SearchBar.svelte`,
  video-list loaders, theme tokens, tests.
- **Dependencies:** URL-state correction should land before or with the extracted component; the
  dialog primitive is needed only if mobile filters use a modal sheet.

### 3. Truthful follow-channel and initial-sync flow

- **User benefit:** Users know whether a channel was followed, whether videos are still loading, and
  what to do after a failure without accidentally creating duplicates.
- **Scope:** Medium to Large.
- **Main files:** backend channel router/service/schema, generated API types, `channels.ts`,
  `AddChannelModal.svelte`, `SyncStatus.svelte`, fake backend/MSW/tests.
- **Dependencies:** Durable sync runs and shared safe API error shape from the broader portfolio plan;
  shared dialog behavior improves the result flow.

### 4. Shared mutation/error/status feedback

- **User benefit:** Watched, Watch Later, queue, save, refresh, and playback failures become visible
  and recoverable instead of silently losing the user's intent.
- **Scope:** Medium.
- **Main files:** API client, shared status UI/store, root layout, video/channel/playlist/player
  components, `ErrorState.svelte`, tests.
- **Dependencies:** Stable API error parsing; dialog primitive for modal-contained actions.

### 5. Shared responsive channel header and complete navigation state

- **User benefit:** Channel identity and actions stop colliding on phones, navigation always shows
  where the user is, and repeated channel pages behave consistently.
- **Scope:** Medium.
- **Main files:** new `ChannelHeader.svelte`, channel route pages, `Sidebar.svelte`, settings layout,
  `TopBar.svelte`, layout tokens, tests.
- **Dependencies:** Navigation terminology decision and the accessible button/link patterns from
  Phase 2.

## 19. Recommended implementation order at a glance

1. **Blockers:** persistent playback; watched/Shorts filter correctness; filter viewport containment.
2. **Keyboard and screen reader:** labelled filters/search; shared dialogs; native card/queue
   semantics; keyboard reorder.
3. **Authentication, forms, navigation:** progressive auth, session recovery, active navigation,
   settings semantics, organization terminology.
4. **Application states:** follow-channel contract, sync lifecycle, mutation feedback, loading/error/
   empty/partial states.
5. **Responsive architecture:** shared channel header, top bar/account reflow, dialog/player checks,
   200% zoom.
6. **Consistency:** shared structural components, tokens, status language, removal of confirmed dead
   client state.
7. **Polish:** typography/spacing/state tuning, portfolio screenshots, complete automated and manual
   release audit.

This order fixes the ability to complete core tasks first, then removes accessibility barriers,
stabilizes entry and navigation, makes system state truthful, and only then consolidates and polishes
the interface.
