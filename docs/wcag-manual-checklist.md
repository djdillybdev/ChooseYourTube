# Manual WCAG release checklist

Run this checklist against the production build at desktop and mobile widths before a tagged release. Automated Axe coverage remains a CI gate, but does not replace these checks.

## Keyboard and focus

- Complete login, navigation, filtering, Watch Later, playback, tag management, and import without a pointer.
- Confirm focus is always visible, follows a logical order, and returns to the trigger after closing a modal or mobile navigation.
- Confirm Escape closes dialogs and navigation without discarding unrelated work.
- Confirm no keyboard trap exists in the player, menus, dialogs, or import flow.

## Screen reader and structure

- Verify every page has a useful title, one clear primary heading, landmarks, and a working skip link.
- Verify controls have meaningful names and state announcements, including filters, pagination, sync status, Watch Later, and import selection.
- Verify validation, authentication expiry, retry, partial failure, and success messages are announced without requiring focus movement.
- Verify video, channel, playlist, and tag relationships remain understandable without visual layout.

## Visual presentation

- Check text and control contrast in every supported theme, including disabled, hover, focus, selected, error, and success states.
- Zoom to 200% and confirm content reflows without horizontal scrolling or hidden controls.
- Check 320 CSS-pixel width, large text, and reduced-motion preferences.
- Confirm information is not conveyed by color, position, or animation alone.

## Media and resilience

- Confirm the player has an accessible name and remains operable when embeds fail or are blocked.
- Confirm loading and synchronization do not unexpectedly move focus or repeatedly interrupt assistive technology.
- Confirm session expiry preserves a safe return path and never exposes another user's content.

Record the browser, assistive technology, viewport, tester, date, failures, and linked fixes in the release notes or release issue.
