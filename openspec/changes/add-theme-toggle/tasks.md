## 1. New icon components

- [x] 1.1 Create `src/core_ui/templates/cotton/icon/sun.html` with the lucide sun SVG (same `{{ attrs }}` passthrough pattern as `cotton/icon/panel_left.html`: 24×24 viewBox, `stroke="currentColor"`, stroke-width 2, round caps/joins)
- [x] 1.2 Create `src/core_ui/templates/cotton/icon/moon_star.html` with the provided lucide moon-star SVG, same passthrough pattern

## 2. Theme state and anti-FOUC on the panel root

- [x] 2.1 In `src/teachers/templates/teachers/base.html`, add to `<html lang="es">`: `x-data` with `dark` (read from `localStorage.theme === 'dark'`) and `toggleTheme()` (flip state + write `localStorage.theme`), `:class="dark && 'dark'"`, and `@toggle-theme.window="toggleTheme()"` (design D2)
- [x] 2.2 Add the one-line inline script in `<head>` (before the stylesheet links) that applies the `dark` class from `localStorage` before first paint (design D4)
- [x] 2.3 Replace `<body class="bg-zinc-50 …">` with `bg-background` so the body background follows the theme (spec: Panel styles support the dark theme)

## 3. Toggle button in the topbar

- [x] 3.1 Wrap the authenticated username block (`base.html:37-39`) in a `flex items-center gap-2` div containing the existing `<span>` and the new toggle, keeping the topbar's two-child `justify-between` layout intact
- [x] 3.2 Add the toggle as `<c-button variant="ghost" type="button" size="icon" aria-label="Cambiar tema" @click="$dispatch('toggle-theme')">` with `<c-icon.sun x-show="!dark" class="size-4" />` and `<c-icon.moon_star x-show="dark" x-cloak class="size-4" />` (design D5)

## 4. Dark-theme style corrections in panel.css

- [x] 4.1 Delete the `:root` variable override block in `src/teachers/static/teachers/css/panel.css` so `--primary`/`--border` resolve from the design system and flip with `.dark` (design D6)
- [x] 4.2 Delete the `body { color: var(--text) }` rule (the `@layer base` rule from `input.css` already applies `text-foreground`)
- [x] 4.3 Change `.card { background: #fff }` to `background: var(--card)`
- [x] 4.4 Make `.messages li` (and `.messages li.error`) dark-aware with explicit `.dark`-scoped color overrides in panel.css; keep light values as default
- [x] 4.5 Sweep `src/teachers/templates/teachers/` for remaining fixed-light utility classes (`bg-white`, `bg-zinc-*`, `text-black`, etc.) that break legibility in dark mode, and replace them with theme-variable utilities

## 5. Build and verification

- [x] 5.1 Run `uv run manage.py tailwind build` and confirm no classes silently dropped (check `bg-background` and `size-4` present in `src/core_ui/static/core-ui/css/output.css`)
- [x] 5.2 Run `uv run manage.py check` (minimum repo verification)
- [ ] 5.3 Manual verification pass in the browser (`uv run manage.py runserver`, login as `teacher1` / dev data): given the panel in light theme, when clicking the toggle, then the page turns dark with no reload, the icon swaps sun → moon-star, and reloading keeps dark with no light flash; clicking again returns to light with the sun icon and reloads stay light; borders, cards, body, and message banners are legible in both themes

## 6. Dark-theme adaptation of design-system components

- [x] 6.1 Convert `cotton/table/index.html` (`divide-gray-200` → `divide-border`) and `cotton/table/body.html` (`divide-gray-200` → `divide-border`, `*:even:bg-gray-100` → `*:even:bg-muted`) to theme tokens that auto-flip with `.dark`
- [x] 6.2 Convert `cotton/table/header.html` and `cotton/table/row.html` (`*:text-gray-900` → `*:text-foreground`)
- [x] 6.3 Create `cotton/quiet_text.html`: single-file link component with semantic quiet-link styling (`text-primary`, `decoration-border decoration-2 underline-offset-4`, `hover:text-primary/80`, `hover:decoration-primary/70`, `focus-visible:ring-4 focus-visible:ring-ring/25`), `href`/`hx-*` passing through `{{ attrs }}`
- [x] 6.4 Replace the inline light-only `<a>` in `course_session_history.html` (inside the `session_list` partialdef) with `<c-quiet_text href="{% url 'teachers:session_detail' session.pk %}">`
- [x] 6.5 Run `uv run manage.py tailwind build --force`, `uv run manage.py check`, and a render smoke test (dashboard, history, both session pages) asserting no `gray-200/gray-900/gray-100` remains in table markup and `<c-quiet_text>` renders as `<a>` with intact `href`
- [ ] 6.6 Manual dark-mode pass in the browser: zebra rows, dividers, header/body text, and the quiet date link are legible on dashboard, course history, and both session-detail pages
