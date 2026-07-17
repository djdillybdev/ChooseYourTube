# Accessibility

ChooseYourTube targets WCAG 2.2 Level AA. Automated tests provide repeatable evidence for this target;
they do not establish complete conformance.

## Implemented behavior

- A skip link and labelled page landmarks support keyboard and screen-reader navigation.
- `:focus-visible` styles provide a visible focus indicator.
- Native dialogs support Escape, focus containment, and focus restoration.
- The mobile navigation drawer makes obscured content inert and closes with Escape.
- Polite live regions announce navigation and background operations. Playback failures use an
  assertive status before the queue advances.
- Authentication forms work without JavaScript, associate labels with inputs, and connect field
  errors through `aria-describedby`.
- Synchronization states use human-readable text, and video actions remain available without hover.
- Reduced-motion preferences disable nonessential route and loading motion.
- Responsive checks cover widths of 320, 375, 768, 1280, and 1440 CSS pixels.

## Automated evidence from 2026-07-16

The deterministic Chromium suite covered login with JavaScript disabled, logout and browser-history
protection, Inbox, Favorites, channel follow and browse, channel refresh and retry, categories, tags,
Watch Later, imports, filters, dialogs, mobile navigation, and responsive reflow.

Axe ran WCAG A and AA rules against principal authenticated routes and open interactive surfaces.
Color contrast checks remained enabled. No serious or critical violations were reported in the tested
fixtures.

Vitest and Testing Library covered primary actions without hover, filter query behavior, form actions,
dialog focus restoration, channel headers, reorder controls, and error and retry presentation. The
isolated full-stack suite covered login and logout, persisted Watch Later state, owner-scoped API
resources, and refresh-token rotation.

## Manual checks still required

Complete and record these checks before making a conformance claim:

- VoiceOver with Safari and at least one other screen-reader and browser combination;
- browser zoom at 200% and text-only enlargement on real rendered pages;
- keyboard operation of the YouTube iframe when playback succeeds, is blocked, and fails;
- touch testing on physical iOS and Android devices;
- visual review of disabled, error, success, selected, hover, and focus states in every theme.

Viewport emulation does not replace real zoom, assistive-technology, or physical-device testing.

## Known limitation

The embedded YouTube player is third-party content. ChooseYourTube supplies a named responsive frame
and handles playback failure, but it cannot inspect or change the accessibility of controls inside the
YouTube iframe.

## Release audit

Use the [manual WCAG checklist](wcag-manual-checklist.md) for each tagged release. Record the tester,
date, operating system, browser, assistive technology and version, viewport or zoom level, failures,
and linked fixes in the release issue or this audit record.
