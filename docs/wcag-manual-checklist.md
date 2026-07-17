# Manual WCAG release checklist

Run this checklist against the production build at desktop and mobile widths before a tagged release.
Automated axe coverage remains a CI gate but does not replace human testing.

## Test record

Record the following information before testing:

- release or commit;
- tester and date;
- operating system and device;
- browser and version;
- assistive technology and version;
- viewport, browser zoom, and text-size settings.

Link each failure to an issue or fix. Store the completed record in the release issue or
[accessibility audit](accessibility.md).

## Keyboard and focus

- Complete login, navigation, filtering, Watch Later, playback, tag management, and import without a
  pointer.
- Confirm that focus is always visible, follows a logical order, and returns to the trigger after a
  dialog or mobile navigation closes.
- Confirm that Escape closes dialogs and navigation without discarding unrelated work.
- Confirm that the player, menus, dialogs, and import flow contain no keyboard traps.

## Screen reader and document structure

- Verify that each page has a useful title, one clear primary heading, appropriate landmarks, and a
  working skip link.
- Verify control names and state announcements for filters, pagination, synchronization, Watch Later,
  and import selection.
- Verify that validation, authentication expiry, partial failure, retry, and success messages are
  announced without requiring focus movement.
- Verify that video, channel, playlist, category, and tag relationships remain understandable without
  the visual layout.

## Visual presentation and reflow

- Check text and control contrast for disabled, hover, focus, selected, error, and success states in
  every supported theme.
- Set browser zoom to 200% and confirm that content reflows without document-level horizontal
  scrolling or hidden controls.
- Check a 320 CSS-pixel viewport, text enlargement, and reduced-motion preferences.
- Confirm that color, position, and animation are not the only ways information is communicated.

## Media and resilience

- Confirm that the player has an accessible name and remains operable when embeds load, fail, or are
  blocked.
- Confirm that loading and synchronization do not move focus unexpectedly or repeatedly interrupt
  assistive technology.
- Confirm that session expiry provides a safe route back to login and never exposes another user's
  content.
- Test key workflows on physical iOS and Android devices.

## Automated evidence from 2026-07-16

- `pnpm check`, `pnpm lint`, and `pnpm test:unit` passed.
- `pnpm test:e2e:fast` passed JavaScript-disabled authentication, keyboard and focus, responsive,
  status, retry, and axe scenarios.
- Reflow fixtures passed at 320, 375, 768, 1280, and 1440 CSS pixels.
- Axe reported no serious or critical issues on the covered principal pages or open filter surface,
  with color contrast enabled.

This automated evidence does not complete screen-reader, physical-device, or real 200% zoom testing.
