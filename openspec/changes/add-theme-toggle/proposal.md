## Why

The teacher panel renders only in light mode even though the design system already ships complete dark-mode CSS variables (`.dark` overrides in `core_ui/input.css`). There is no way for teachers to activate the dark theme. The topbar currently shows the username as plain text, leaving room for an appearance control, and the Unfold admin has a theme switch the panel lacks. This change adds a light/dark toggle button next to the username and fixes the remaining hardcoded light-only styles.

## What Changes

- Add a ghost icon button in the topbar, next to the username (`teachers/base.html`), that toggles the theme.
- The button shows the **sun icon in light theme** and the **moon-star icon in dark theme** (two new cotton icon components using the provided lucide SVGs).
- Toggle is 100% client-side with Alpine: button does `$dispatch('toggle-theme')`; `<html>` holds an `x-data` scope that reactively adds/removes the `.dark` class (mirrors the existing `toggle-sidebar` dispatch pattern).
- Theme persists in `localStorage` (key `theme`), following the existing sidebar persistence precedent.
- A one-line inline script in `<head>` applies `.dark` from `localStorage` before first paint (anti-FOUC).
- Fix light-only styles so the dark theme actually covers the panel: `<body>` class `bg-zinc-50` → `bg-background` in `teachers/base.html`; audit `teachers/css/panel.css` for hardcoded light colors and replace them with design-system variables.
- Rebuild Tailwind CSS after adding new utility classes.

## Capabilities

### New Capabilities
- `theme-toggle`: light/dark appearance switching for the teacher panel — toggle button placement and behavior, sun/moon icon states, `.dark` class application on `<html>`, localStorage persistence, flash-free load, and dark-compatible panel styling.

### Modified Capabilities

(none — no existing requirements change; the toggle adds new behavior)

## Impact

- `src/teachers/templates/teachers/base.html` — topbar markup (new wrapper + button), `<html>` attributes, inline anti-FOUC script, body class fix.
- `src/core_ui/templates/cotton/icon/sun.html`, `moon_star.html` — new icon components.
- `src/teachers/static/teachers/css/panel.css` — audit and fix hardcoded light colors.
- `src/core_ui/static/core-ui/css/output.css` — rebuilt via `uv run manage.py tailwind build`.
- No models, views, URLs, or dependencies change (Alpine is already vendored and loaded in the panel base).

## Non-goals

- No system/auto-follow mode (`matchMedia`) — binary light/dark only; the Unfold-style "System" option is deferred.
- No server-side or per-user persistence (cookies, session, DB) — `localStorage` only.
- No changes to the Unfold admin theme.
- No new dark palettes — only make existing pages render correctly under the `.dark` variables.
