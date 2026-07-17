# Accessibility

ChooseYourTube targets WCAG 2.2 AA. Automated checks support this target but are not a claim of full
conformance.

## Implemented foundation

- Skip-to-content navigation and labelled page landmarks.
- Visible `:focus-visible` indicators and reduced-motion overrides.
- Keyboard-operable native dialogs with Escape handling and focus restoration.
- A mobile navigation drawer that makes obscured content inert and supports Escape.
- Polite live announcements for navigation and background operations; playback failures use an
  assertive status before the queue advances.
- Explicit labels for mobile filters and authentication/account controls.
- Responsive layouts tested at 320 px, 375 px, 768 px, 1280 px, and 1440 px.
- Native, labelled auth forms that work without JavaScript and associate field errors with inputs.
- Human-readable synchronization states, explicit keyboard reordering, and visible non-hover video
  actions.
- Axe coverage for authenticated routes, open filters, dialogs, and contrast-sensitive controls.

## Audit record — 2026-07-16

Automated validation was run in Chromium against the deterministic fake backend:

- Playwright covered login with JavaScript disabled, logout/history protection, Inbox, Favorites,
  channel follow and browse, channel refresh and retry, categories, tags, Watch Later, imports,
  filters, dialogs, mobile navigation, and responsive reflow.
- Axe ran WCAG A/AA rules on login, Inbox, Favorites, channel, Watch Later, player, imports, and
  organization settings, with color contrast enabled. The open filter surface was scanned
  separately as an interactive state.
- Viewports 320, 375, 768, 1280, and 1440 CSS pixels were checked for document-level horizontal
  overflow. Dialog content is internally scrollable in constrained height and route progress honors
  `prefers-reduced-motion`.
- Vitest/Testing Library covered primary actions without hover, filter query semantics, form actions,
  dialog focus restoration, channel headers, reorder controls, and retry/error presentation.
- The isolated seeded full-stack suite covered password login/logout, persisted Watch Later state,
  owner-scoped API resources, and refresh-token rotation.

The following checks require a human before any accessibility-conformance statement. Until they are
recorded, public project material describes WCAG 2.2 AA as a target rather than a certification:

- VoiceOver with Safari and at least one second screen reader/browser combination.
- A real 200% browser-zoom and text-only enlargement pass; viewport emulation is not equivalent.
- Keyboard verification of the third-party YouTube iframe when the embed is available, blocked, and
  fails during playback.
- Touch testing on physical iOS and Android hardware.
- Visual review of every disabled/error/status color combination beyond the Axe-covered fixtures.

Known limitation: the embedded YouTube player is third-party UI. ChooseYourTube provides a named,
responsive frame and a playback-failure path, but cannot control the semantics of YouTube's internal
iframe controls.

## Manual release audit instructions

Before v1.0, complete the outstanding checks above using
[`wcag-manual-checklist.md`](./wcag-manual-checklist.md). Record the tester, operating system,
browser, assistive technology and version, viewport/zoom, failures, and linked fixes in this file or
the release issue.
