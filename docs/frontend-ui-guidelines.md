# Frontend UI guidelines

These conventions keep the interface consistent, accessible, and focused on subscription viewing.
Apply them to new features and components being changed.

## Layout and shared components

- Use the spacing, content width, border, radius, focus, status, and muted-content tokens in
  `frontend/src/routes/layout.css`.
- Give primary content 1rem side padding on mobile and 1.5rem from the small breakpoint upward.
- Use a centered readable video list. Do not add recommendation panels, trending modules, engagement
  counters, masonry layouts, or dense thumbnail grids.
- Reuse `PageHeader`, `ChannelHeader`, `DialogShell`, `ErrorState`, `EmptyState`, `StatusBadge`, and
  `VideoFilters` for their existing roles.
- Keep route data loading in route loaders rather than presentation components.
- Test muted text against its actual surface. Low-opacity text is limited to decoration that is not
  needed to understand or operate the interface.

## Action hierarchy

- Use primary styling for the main task on a page or dialog, such as **Follow channel** or **Save**.
- Use neutral or outline styling for ordinary actions such as **Retry** or **View channel**.
- Use ghost styling for low-frequency reversible actions such as **Edit** or **Refresh**.
- Give destructive actions explicit error styling and a confirmation dialog. Initial focus belongs on
  **Cancel**.
- Give icon-only controls a complete accessible name and a minimum 24 by 24 CSS-pixel target. Primary
  touch actions should approach 44 by 44 pixels.

## Forms

Associate every native label with its control through `for` and `id`. Put optional instructions before
the control and an inline error after it. Invalid controls set `aria-invalid="true"` and reference the
error through `aria-describedby`.

Request-level failures use an alert summary. Enhanced forms move focus to that summary. Disabled and
pending controls keep an explanatory label; a spinner does not replace all text.

## Status and feedback

- Write synchronization states as plain language: "Sync queued", "Sync in progress", "Sync
  succeeded", "Sync partially completed", and "Sync failed". Do not rely on color alone.
- Send mutation success through the global polite status host.
- Keep blocking failures beside the failed action with `role="alert"`. Offer retry only when the
  operation is safe to repeat.
- Preserve loaded content during background refresh.
- Keep progress motion restrained and respect `prefers-reduced-motion`.

## Review checklist

Before merging an interface change, verify keyboard operation, visible focus, accessible names,
loading and error states, narrow-width reflow, reduced motion, and behavior without hover. Add or
update component and Playwright tests for the affected workflow.
