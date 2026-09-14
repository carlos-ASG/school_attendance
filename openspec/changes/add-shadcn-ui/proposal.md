# add-shadcn-ui

## Why

The teacher panel is unstyled plain HTML with a hand-written `panel.css`; login is a bare form. The project needs a maintainable design system: component-based templates (django-cotton), shadcn-style components (shadcn/django over Tailwind + Alpine), a styled login (django-allauth + the shadcn allauth block), and a proper navigation menu for the panel.

## What Changes

- Add **django-cotton** as the component engine (`src/core_ui/templates/cotton/` in the dedicated `core_ui` app, auto-config loader injection).
- Add the **shadcn/django** design system via `uvx shadcn_django@latest init` + `add` (copied, owned component source). Tailwind compiled with **django-tailwind-cli** (uv-only, no node); Alpine.js vendored into static like htmx.
- Adopt **django-allauth** for authentication and style it with the shadcn allauth block (17 templates in `templates/account/`). **BREAKING**: login moves from `teachers:login` (django.contrib.auth LoginView) to allauth's account login flow; URL `/teacher/login/` is retired in favor of allauth routes. Username login is preserved (`ACCOUNT_LOGIN_METHODS = {'username'}`) and post-login role routing (staff → admin, teacher → panel) is preserved via allauth adapter/settings.
- Add a **shadcn navigation menu** to the panel chrome (replaces the bare `<nav>` in `teachers/base.html`).
- Translate all adopted component/template copy to **Spanish** (panel spec already mandates Spanish).
- Capture the patterns in two opencode skills (`django-cotton`, `shadcn-django`) + AGENTS.md trigger rows. *(Done in this session.)*

## Capabilities

### New Capabilities
- `ui-components`: the repo's component-based UI system — django-cotton setup/conventions (`templates/cotton/`, slots, `c-vars`, variants), shadcn/django component ownership (CLI-copied source), Tailwind build tooling (django-tailwind-cli), Alpine.js delivery (vendored), theming via CSS variables, Spanish copy, and the boundary that Unfold continues to own `/admin/`.

### Modified Capabilities
- `teacher-panel`: authentication requirement changes from Django built-in LoginView to django-allauth (username login kept, password-reset flows added); new requirement for panel navigation menu; panel chrome styled with the new component system.

## Impact

- **Dependencies**: `django-cotton`, `django-allauth`, `django-tailwind-cli` via `uv`; `tw-animate-css` manual CSS download; Alpine.js vendored file. Verify allauth ↔ Django 6.1 compatibility at `uv add`.
- **Settings** (`src/config/settings.py`): `INSTALLED_APPS` (+ cotton, allauth, allauth.account, tailwind-cli app), `MIDDLEWARE` (+ allauth AccountMiddleware), `AUTHENTICATION_BACKENDS`, allauth `ACCOUNT_*` settings, `TEMPLATES[0]['DIRS']`, `LOGIN_URL`/redirects.
- **Templates**: new `src/core_ui/templates/cotton/`, `src/core_ui/templates/account/` (+ `base.html`) inside the `core_ui` design-system app; `teachers/base.html` nav replaced; `teachers/login.html` retired.
- **Views/URLs**: `src/teachers/views/auth.py` LoginView/LogoutView replaced by allauth views (redirect logic moves to allauth adapter); `src/teachers/urls.py` loses login/logout routes.
- **Build workflow**: `uv run manage.py tailwind start` watcher alongside `runserver`.
- **Signup**: closed by business rule (accounts created via admin) — the login-page link is removed and `is_open_for_signup()` returns `False`; signup templates are kept for potential future use.
- Existing HTMX fragments and `src/school/components.py` (unfold admin charts) are untouched.

## Non-goals

- No restyling of the Unfold admin site (it keeps its own theme/components).
- No email-based login or email verification mandate in dev (username login stays; verification `optional`).
- No migration of existing `{% partialdef %}` HTMX fragments to cotton components.
- No signup for teachers (accounts are managed via admin); signup template exists but is not linked.
- No dark-mode toggle or additional UI pages beyond login + navigation.
