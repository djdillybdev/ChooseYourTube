# ChooseYourTube frontend UI guidelines

These conventions keep the interface clear, accessible, and deliberately quieter than YouTube.
They apply to new work and to touched components; they are not a reason for cosmetic rewrites.

## Layout and tokens

- Use the spacing, content-width, border, radius, focus, status, and muted-content tokens in
  `frontend/src/routes/layout.css`. Primary content uses 1rem mobile side padding and 1.5rem from the
  small breakpoint upward.
- Use a centered readable list for videos. Do not introduce masonry, recommendations, engagement
  modules, or dense thumbnail grids.
- `PageHeader`, `ChannelHeader`, `DialogShell`, `ErrorState`, `EmptyState`, `StatusBadge`, and
  `VideoFilters` are the shared structural primitives. Keep data loading in route loaders.
- Use full `text-base-content` on the tinted page background and test any muted text against its
  actual surface. Lower-opacity text is reserved for large,
  nonessential decorative marks that are not required to understand or operate the UI.

## Action hierarchy

- Primary: the single main task on a page or in a dialog, such as Follow channel or Save.
- Neutral/outline: ordinary actions such as Retry or View channel.
- Ghost: low-frequency, reversible actions such as Edit or Refresh when it is not the main task.
- Destructive: use explicit error styling, a confirmation dialog, and initial focus on Cancel.
- Icon-only controls need a complete accessible name and a minimum 24 by 24 CSS-pixel target;
  primary touch actions should approach 44 by 44 pixels.

## Form field pattern

Each field uses a native label associated by `for` and `id`, optional descriptive text, and an inline
error. Invalid controls set `aria-invalid="true"` and reference the error using `aria-describedby`.
Request-level errors use an alert summary and enhanced forms move focus to it. Disabled and pending
controls keep readable labels; a spinner never replaces all explanatory text.

## Status and feedback

- Synchronization states are written as human language: “Sync queued,” “Sync in progress,” “Sync
  succeeded,” “Sync partially completed,” and “Sync failed.” Color is supporting information only.
- Mutation success goes through the global polite status host. Blocking failures stay beside the
  failed action with `role="alert"` and a safe retry when one is available.
- Background refresh preserves existing content. Loading progress is restrained and respects
  `prefers-reduced-motion`.
