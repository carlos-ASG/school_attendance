# add-shadcn-ui — Design

## Context

The teacher panel (`src/teachers/`) is plain HTML + hand-written `panel.css`; login is
`django.contrib.auth` `LoginView` at `/teacher/login/` with staff→admin / teacher→dashboard
redirect logic (`src/teachers/views/auth.py`). The repo is pure-uv (no node), vendors
`htmx.min.js`, and uses Django 6 native `partialdef` fragments (see `django6-htmx` skill).
Unfold themes `/admin/` and owns `src/school/components.py` (admin charts). UI language is
Spanish (spec `teacher-panel` requirement). Auth requirements live in spec `teacher-panel`.

The patterns live in two skills created for this repo: `django-cotton` (framework layer)
and `shadcn-django` (design system layer); they are the reference for implementation.

## Goals / Non-Goals

**Goals:**

- Component-based UI: django-cotton engine + shadcn/django components, Spanish copy.
- Styled login via django-allauth + the shadcn allauth block, with password-reset flows.
- Navigation menu (shadcn) in the panel chrome.
- Tailwind built without node; Alpine vendored; minimal deviation from repo habits.

**Non-Goals:**

- Restyling Unfold admin; touching `src/school/components.py` or existing HTMX fragments.
- Email login, forced email verification, signup flows for teachers (template exists, unlinked).
- Dark-mode toggle, extra pages.

## Decisions

1. **Component engine: django-cotton (auto-config)** — the repo's templates stay DTL;
   cotton injects its loader chain + builtins into `TEMPLATES` automatically
   (cached.Loader included). Alternatives considered: `django-components` (backend-class
   components, heavier), slippers/DTL includes (no slots, no dynamic attrs). Cotton wins
   because shadcn-django is built on it and its syntax maximizes IDE support.
2. **Design system: shadcn/django, CLI-copied (you own the code)** — `uvx shadcn_django init`
   then `add <component>`. Components land in `templates/cotton/` and are edited in-repo
   (Spanish translation is part of adoption). Alternative: prebuilt kits (cotton-ui) —
   less aligned with the shadcn docs the user adopted.
3. **Component + auth template location: the `core_ui` app** — `src/core_ui/templates/cotton/`,
   `src/core_ui/templates/account/` (plus its `base.html`). Django discovers app template dirs
   natively (cotton 2.7.2 scans every installed app's `templates/`; no `TEMPLATES[0]['DIRS']`
   needed), `core_ui` precedes `allauth` in `INSTALLED_APPS` so the copied `account/` templates
   shadow allauth's builtins. Alternative: project-root `templates/` — rejected after initial
   implementation: a dedicated app keeps the design system reusable by future apps (e.g. a
   students panel) without root-level files.
4. **Tailwind: django-tailwind-cli (uv-only)** — `manage.py tailwind install_cli/start`
   keeps the repo npm-free; `tw-animate-css` via manual CSS download. Alternative: npm +
   `@tailwindcss/cli` (standard shadcn path) — rejected: introduces node tooling against
   repo convention. The watcher runs alongside `runserver` in dev.
5. **Alpine.js: vendored static file** — matches existing vendored `htmx.min.js`
   (`<script defer>` in panel `<head>`). Alternative: CDN — rejected (repo avoids CDNs).
   Alpine and HTMX coexist (no conflict; both defer).
6. **Auth: django-allauth with username login preserved** — `ACCOUNT_LOGIN_METHODS =
   {'username'}` keeps seeded teacher accounts working; `ACCOUNT_EMAIL_VERIFICATION =
   'optional'` for the dev console-email setup; `AccountMiddleware` added (required);
   `AUTHENTICATION_BACKENDS` gets allauth's `AuthenticationBackend` before `ModelBackend`.
   The staff/teacher post-login routing moves from `LoginView.get_success_url()` into an
   allauth `DefaultAccountAdapter` subclass overriding `get_login_redirect` (staff →
   `admin:index`, else → `teachers:dashboard`). LOGIN_URL/redirect settings point at
   allauth route names. Alternative considered: restyle the existing `AuthenticationForm`
   login — rejected (user chose full allauth for the styled flows: logout, password reset,
   change/set). Login/logout/reauthenticate/password templates come from the allauth block;
   `signup*` are installed but unlinked (teachers are created in admin).
7. **Panel navigation: shadcn navigation-menu component** — Alpine dropdown nav wired into
   `teachers/base.html` replacing the bare `<nav>`; Spanish labels (Panel, Cursos,
   Cerrar sesión); logout stays a POST form (`hx-boost="false"`), not an HTMX swap.
   Alternative: plain links / dropdown-menu component — navigation-menu matches the
   chosen shadcn docs page.
8. **Fragments: partialdef remains the HTMX fragment mechanism** — cotton components may
   compose inside fragments; `render_component()` only for single-component responses
   (see `django-cotton` skill). Existing fragment behavior must stay byte-identical.
9. **Shared static assets: the `core_ui` app's static dir** — app static files namespaced
   `core-ui/` (`css/output.css`, `css/tw-animate.css`, `js/alpine.min.js`); the Tailwind
   input CSS lives at `src/core_ui/input.css`; app assets (`teachers/css/panel.css`,
   `htmx.min.js`) stay app-level until individually migrated.

## Risks / Trade-offs

- [django-allauth vs Django 6.1 (very new)] → resolve at `uv add` (pick a version that
  supports 6.1); verify with `uv run manage.py check` + `migrate` before proceeding.
- [`shadcn_django init` behavior in this src-layout repo is unverified (what it writes,
  whether it edits settings)] → run it, inspect `git diff`, reconcile with settings;
  `uv run manage.py check` after.
- [Component filenames may be kebab-case from the CLI] → inspect after `add`; if they
  are kebab, set `COTTON_SNAKE_CASED_NAMES = False` (one-line settings change) instead of
  renaming CLI output.
- [Tailwind CLI + tw-animate-css manual download paths] → follow django-tailwind-cli +
  tw-animate-css manual-install docs; pin the CSS file into the shared `static/` dir.
- [Cotton's loader injection changes template loading for the whole project] → run the
  byte-diff harness (`django6-htmx` skill) on panel pages after installation to prove
  existing output is unchanged.
- [Forgetting allauth `AccountMiddleware` or context processors → allauth system check
  E035 / template errors] → add middleware in the same commit as `INSTALLED_APPS`.
- [LOGIN_URL remnants referencing `/teacher/login/`] → audit `LOGIN_URL`,
  `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`, and any `reverse('teachers:login')`.

## Migration Plan

1. Install deps (`uv add django-cotton django-allauth django-tailwind-cli`), configure
   settings, `uv run manage.py check` — tree still renders as before (harness diff clean).
2. `uvx shadcn_django init`; set up django-tailwind-cli; vendor Alpine; wire `<head>`;
   `uv add` the initial components (`card button input label checkbox alert badge
   separator navigation_menu`) + `allauth` block; translate copy to Spanish.
3. Migrate auth: allauth settings + adapter; replace `teachers/views/auth.py` login/logout
   with allauth routes; delete `teachers/login.html`; update nav/logout wiring.
4. Add navigation menu to `teachers/base.html`; restyle panel chrome progressively
   (base template only in this change).
5. Verify: `uv run manage.py check`, byte-diff harness on untouched pages, manual login
   flow (username login, logout, staff/teacher redirect), tailwind build succeeds.
6. Rollback: `git revert` per step; before removing allauth app, `uv run manage.py
   migrate account zero` (allauth adds DB tables; no project models change).

## Open Questions

- Exact django-tailwind-cli settings/input-CSS paths for Tailwind v4 + where the CLI
  expects `tw-animate-css` import — resolve during implementation against its docs.
- Whether `shadcn_django init` output needs manual reconciliation with the repo's
  `TEMPLATES`/`INSTALLED_APPS` (inspect the diff it produces).
- Confirm the allauth version supporting Django 6.1 and any required
  `ACCOUNT_*` defaults beyond the ones listed above.
