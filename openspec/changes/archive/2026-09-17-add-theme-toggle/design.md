## Context

The teacher panel (`src/teachers/templates/teachers/base.html`) renders its chrome entirely from the `core_ui` design system, whose input CSS already defines a complete dark palette under a class-based `.dark` selector (`@custom-variant dark (&:is(.dark *))`, `.dark { … }` overrides in `src/core_ui/input.css`). Nothing lets users activate it: the topbar shows the username as a plain `<span>` (base.html:38), and no theme state exists anywhere.

Two precedents in the repo shape this design:

- **Unfold admin** (investigated in `.venv/.../unfold/`): theme switching is 100% client-side — Alpine `switchTheme()` persists via `Alpine.$persist` to localStorage, and an `x-bind:class` on `<html>` reactively applies `dark`; the server only renders an initial class from its `THEME` config to avoid first-paint flash (`skeleton.html:18`).
- **The panel's own sidebar toggle**: a topbar button dispatches a window event (`$dispatch('toggle-sidebar')`, `cotton/topbar/trigger.html:4`) consumed by a `@toggle-sidebar.window` listener on the element that owns state, which itself persists to `localStorage` (`cotton/sidebar/index.html:5-13`).

Constraint: no node/npm (Tailwind via django-tailwind-cli); Alpine is vendored and loaded in the panel base (`base.html:11`); UI copy is Spanish.

## Goals / Non-Goals

**Goals:**

- One-click light/dark toggle next to the username in the topbar, zero page reloads.
- Sun icon in light theme, moon-star icon in dark theme, swapping reactively.
- Theme persists across full loads and in-panel navigation.
- Dark theme actually covers the panel (fix hardcoded light-only styles).
- Stay inside the existing design system (cotton components, Tailwind variables, Alpine patterns already in use).

**Non-Goals:**

- No system/auto mode (`matchMedia`) — binary toggle only.
- No server-side or per-user persistence — `localStorage` only.
- No changes to Unfold admin.
- No new dark palettes — reuse the existing `.dark` variable set.

## Decisions

### D1: Client-side Alpine toggle, not URL navigation or POST

A theme switch is a client state change (one class on `<html>`); routing it through the server is the wrong tool: a full reload for a CSS swap, a new URL + view + redirect for nothing, and GET-with-side-effects semantics that browsers/HTMX may prefetch. POST adds the same reload with more ceremony. This matches Unfold's own implementation (no navigation anywhere in its theme path). Chosen: click → mutate Alpine state + `localStorage`.

### D2: State lives in an `x-data` scope on `<html>`; button communicates via `$dispatch('toggle-theme')`

The `.dark` class must sit on the root (everything must be a `.dark *` descendant per the custom variant), but the button is deep in the topbar — the exact topology the sidebar already solves with its dispatch pattern. `<html>` gets:

```html
x-data="{
  dark: localStorage.getItem('theme') === 'dark',
  toggleTheme() {
    this.dark = !this.dark;
    localStorage.setItem('theme', this.dark ? 'dark' : 'light');
  }
}"
:class="dark && 'dark'"
@toggle-theme.window="toggleTheme()"
```

The button needs no `x-data` of its own — it inherits the root scope. Alternative rejected: `Alpine.store('theme')` registered in `alpine:init` — more moving parts for no benefit at this size; `x-data` on the root is the in-repo precedent (sidebar).

### D3: Persistence via `localStorage` key `theme` (`light` / `dark`)

Mirrors the sidebar's `sidebar-open` localStorage key. Read once by `x-data` init and again by the anti-FOUC script — both derive from the same source so they can't disagree. Alternatives rejected: cookie read server-side (needs view/context machinery for zero UX gain at this scope), per-user DB setting (out of scope).

### D4: Anti-FOUC with a one-line inline script in `<head>`, not server-rendered class

```html
<script>document.documentElement.classList.toggle('dark', localStorage.getItem('theme') === 'dark')</script>
```

Placed in `<head>` before the stylesheet links; blocking by nature and runs before first paint — same effect as Unfold's server-rendered class without adding a cookie/view/context-processor. Alternatives rejected: `x-cloak` on the body (hides the whole panel until Alpine inits); server-side class via `THEME`-style config (backend machinery this change deliberately avoids).

### D5: Icon swap with `x-show` + `x-cloak` defaulting to light

Icon components pass `{{ attrs }}` straight onto the `<svg>` (`cotton/icon/panel_left.html:1`), so the directives attach to the icon elements directly, and they inherit `dark` from the root scope:

```html
<c-button variant="ghost" type="button" aria-label="Cambiar tema"
          @click="$dispatch('toggle-theme')">
  <c-icon.sun x-show="!dark" class="size-4" />
  <c-icon.moon_star x-show="dark" x-cloak class="size-4" />
</c-button>
```

`@click` passes through cotton attrs unmodified (only the `:` prefix needs the `::` escape; `@` is untouched — existing panel precedent uses `::disabled` on `c-button`). The moon gets `x-cloak` so the pre-Alpine default state matches the light assumption (server-rendered HTML can't know the stored theme). Alternative rejected: Tailwind `hidden` + `x-show` — Alpine clears the inline display, letting `.hidden` win again (known interplay gotcha); `x-cloak` is removed by Alpine at init and then `x-show` fully owns visibility. Accepted artifact: for a dark-mode user, the sun icon shows for the brief pre-Alpine window on first paint.

Files: new `cotton/icon/sun.html` and `cotton/icon/moon_star.html` (snake_case → `<c-icon.moon_star />`), same lucide stroke attributes as existing icons, sized `size-4` like other in-content icons.

### D6: Fix the light-only hardcoding in the panel chrome

Two concrete sources were identified by reading the code:

1. `base.html:13` — `<body class="bg-zinc-50 …">`: a fixed light utility overriding the theme background. Fix: `bg-background` (var-driven; flips with `.dark`).
2. `src/teachers/static/teachers/css/panel.css` — and this one is worse than "light colors":
   - Its `:root { --primary: #4f46e5; --border: #e2e8f0; --text: #1e293b; … }` redefines variable names that **collide with the design system** (`--primary`, `--border`). It loads *after* `output.css` (base.html:8-9), and as `:root` has the same specificity as `.dark`, these overrides would keep light values alive in dark mode — borders and primary color would silently never darken. Fix: delete the `:root` block entirely so `var(--border)`/`var(--primary)` resolve to the design-system variables and follow the theme.
   - `body { color: var(--text) }` — unlayered rule beats the `@layer base` `bg-background text-foreground` from `input.css`; body text would stay `#1e293b` in dark. Fix: delete the rule (the base layer already covers it).
   - `.card { background: #fff }` → `background: var(--card)`.
   - `.messages li` pastel greens/reds (`#dcfce7`/`#fee2e2`) — white-ish backgrounds that would sit under near-white dark foreground text. Fix: keep the semantic colors but add explicit `.dark`-scoped values in panel.css (plain CSS file; scoped overrides, no Tailwind build dependency for this file).
   - `.status-*` solid intent buttons (green/amber/blue/gray) stay as-is — solid background + light text stays legible under both themes.

Plus a sweep of panel templates for other fixed-light utilities (`bg-white`, `bg-zinc-*`, `text-black`, …) replacing them with theme-variable utilities where they affect legibility.

### D7: Toggle stays inline in `base.html` (no new cotton component)

Per the requester: this is intentionally a quick, movable change. The toggle is a self-contained wrapper div (name + button) inside the authenticated block — trivially extractable later into a `cotton/topbar/user.html` (`<c-topbar.user />`) or a `{% block topbar_actions %}` when needed. Decision recorded so the extraction path is known, not built.

### D8: Dark-theme adaptation of design-system components uses semantic tokens, not literal `dark:` classes

Follow-up scope added during apply: the `c-table` component still carried the hardcoded HyperUI grays from its original source (`divide-gray-200` on `index.html`/`body.html`, `*:text-gray-900` on `header.html`/`row.html`, `*:even:bg-gray-100` on `body.html`), which leave table dividers, text, and zebra rows light-only in dark mode. Fix: convert them to the same semantic tokens `c-detail_list` already uses (`divide-border`, `*:text-foreground`, `*:even:bg-muted`), which auto-flip with `.dark` and keep zebra/divider behavior identical across components. Alternative rejected: pasting the literal HyperUI dark variants (`dark:divide-gray-700`, `dark:*:text-white`, `dark:*:even:bg-gray-800`) — pixel-equivalent but introduces a second hard-coded gray scale parallel to the oklch tokens.

The light-only inline "session detail" link in `course_session_history.html` (the HyperUI "quiet text" link: indigo/slate literals, no dark variants) is extracted into a new single-file design-system component `cotton/quiet_text.html` with the equivalent semantic styling (`text-primary` — the token is literally indigo hue 276.966, `decoration-border`, `hover:text-primary/80`, `hover:decoration-primary/70`, `focus-visible:ring-ring/25`), with `href`/`hx-*` proxied through `{{ attrs }}`. It is used inside the `session_list` partialdef; cotton composes inside partialdef fragments and the component has no Alpine directives, so HTMX re-init needs nothing. `c-detail_list` was inspected and found already token-based (divide-border / *:even:bg-muted / text-foreground / text-muted-foreground) — it already renders the user's target dark design and is left untouched.

## Risks / Trade-offs

- **[panel.css `:root` collision silently defeats dark mode]** → the `:root` block is deleted, not patched; verified by checking borders/cards flip with `.dark` after the change.
- **[Alpine loads `defer` → brief pre-init window]** → anti-FOUC script is non-Alpine (plain JS) so the dark class is correct before paint; only the icon may lag one frame behind (D5 accepted artifact).
- **[localStorage is per-browser, not per-user]** → accepted non-goal; a teacher on a shared machine sees the last browser-wide choice. Extension path (cookie + server render) is documented but not built.
- **[`theme` key collides with other app conventions?]** → namespaced only by convention like `sidebar-open`; key is `theme`, values strictly `light`/`dark`; no collision with `sidebar-open`.
- **[Tailwind stale CSS drops unknown classes silently]** → run `uv run manage.py tailwind build` after any class additions; no new Tailwind utilities are expected beyond what already exists (`bg-background`, `size-4` are in use), but the rebuild is part of the task list regardless.
- **[Unfold admin is untouched]** → admin has its own theme stack (`admin-theme` spec); no shared surface with the panel beyond Tailwind input, which this change doesn't alter.

## Migration Plan

No data, dependency, or URL changes — template/CSS-only. Deploy order irrelevant; rollback is reverting the files. The Tailwind rebuild is required on deploy (fresh `output.css`).

## Open Questions

None blocking. Deferred by design: "System/auto" third state, cookie-based server-rendered initial theme, and extraction of the toggle into a reusable cotton component.
