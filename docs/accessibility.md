# Accessibility

ChooseYourTube targets WCAG 2.2 AA. Phase 5 establishes the application-level accessibility
foundation; Phase 6 adds automated axe coverage in Playwright.

## Implemented foundation

- Skip-to-content navigation and labelled page landmarks.
- Visible `:focus-visible` indicators and reduced-motion overrides.
- Keyboard-operable native dialogs with Escape handling and focus restoration.
- A mobile navigation drawer that makes obscured content inert and supports Escape.
- Polite live announcements for navigation and background operations; playback failures use an
  assertive status before the queue advances.
- Explicit labels for mobile filters and authentication/account controls.
- Responsive layouts targeted at 375 px, 768 px, and 1280 px.

## Manual release audit

Before v1.0, verify login, inbox, channel, playlist, player, imports, sync activity, and account
settings using keyboard-only navigation and VoiceOver/Safari. Repeat at 200% zoom, 375 px, 768 px,
and 1280 px widths, with reduced motion enabled. Record the audit date and any accepted limitations
here when the Phase 6 deterministic test stack is available.
