# add-shadcn-ui — Tasks

## 1. Dependencies and cotton installation

- [ ] 1.1 Verify compatibility: `uv add django-cotton django-allauth django-tailwind-cli`; confirm the resolved django-allauth version supports Django 6.1 (run `uv run manage.py check` after wiring step 1.3; roll back the `uv add` if no compatible allauth exists)
- [ ] 1.2 Capture baseline: copy `db.sqlite3` to `/tmp/work/db.sqlite3`, seed via `seed_dev_data`, snapshot it, and capture pre-change rendered HTML of dashboard/course/session/login pages per the byte-diff harness (django6-htmx skill)
- [ ] 1.3 Add `django_cotton` to `INSTALLED_APPS`; set `TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']`; run `uv run manage.py check` and confirm `templates` loading still works
- [ ] 1.4 Byte-diff the captured pages after cotton installation — output must be unchanged (Given an existing panel page, When rendered with the cotton loader chain active, Then the HTML is byte-identical to the pre-change capture)

## 2. Build tooling and assets

- [ ] 2.1 Configure django-tailwind-cli per its docs (Tailwind v4 input CSS with `@import "tailwindcss";`, `STATICFILES_DIRS` for the shared project `static/` dir, settings for the compiled `output.css` path)
- [ ] 2.2 Download `tw-animate-css` stylesheet manually (no npm) into the shared `static/` and import it from the input CSS per the tw-animate-css manual-install docs
- [ ] 2.3 Run `uv run manage.py tailwind install_cli` and `uv run manage.py tailwind build`; confirm the compiled CSS appears in the shared `static/` dir
- [ ] 2.4 Vendor Alpine.js: download the 3.x CDN build to the shared `static/` as `alpine.min.js` (Given no network at runtime, When a panel page loads, Then Alpine initializes from the vendored file)

## 3. shadcn/django scaffold and components

- [ ] 3.1 Run `uvx shadcn_django@latest init` from the repo root; inspect the resulting `git status`/diff; reconcile anything it wrote with existing settings; `uv run manage.py check`
- [ ] 3.2 Run `uvx shadcn_django@latest add card button input label checkbox alert badge separator navigation_menu allauth`; confirm components land in `templates/cotton/` with snake_case filenames compatible with the default `COTTON_SNAKE_CASED_NAMES = True` (set `False` in settings instead of renaming if the CLI writes kebab-case)
- [ ] 3.3 Confirm the allauth block's 17 templates exist in `templates/account/` and the base template `<head>` links the compiled CSS plus the vendored Alpine script

## 4. Spanish translation of adopted code

- [ ] 4.1 Translate user-visible copy in the copied cotton components and `templates/account/` templates to Spanish (Sign In → Iniciar sesión, Password → Contraseña, Remember me → Recordarme, Forgot Password? → ¿Olvidaste tu contraseña?, Sign Out → Cerrar sesión, Email → Correo electrónico); keep code identifiers/URL paths in English

## 5. django-allauth migration

- [ ] 5.1 Add allauth config to `src/config/settings.py`: `INSTALLED_APPS` (+ `allauth`, `allauth.account`), `MIDDLEWARE` (+ `allauth.account.middleware.AccountMiddleware`), `AUTHENTICATION_BACKENDS` (allauth `AuthenticationBackend` then `ModelBackend`), `ACCOUNT_LOGIN_METHODS = {'username'}`, `ACCOUNT_EMAIL_VERIFICATION = 'optional'`, allauth account adapter setting, updated `LOGIN_URL`/`LOGIN_REDIRECT_URL`/`LOGOUT_REDIRECT_URL`; run `uv run manage.py check` (Given settings updated, When check runs, Then no allauth system-check errors such as E035)
- [ ] 5.2 Add the account adapter subclass that preserves role routing (Given a staff user logs in, Then redirect to the admin site; Given a teacher logs in, Then redirect to the teacher panel dashboard) replacing `LoginView.get_success_url`
- [ ] 5.3 Run `uv run manage.py migrate` (allauth creates its tables); update `src/teachers/urls.py` and `src/teachers/views/auth.py`: remove `LoginView`/`LogoutView`/`HomeRedirectView` routing to `/teacher/login/` and wire allauth's `account_login`/`account_logout` (root home redirect to allauth login/dashboard as today)
- [ ] 5.4 Delete `src/teachers/templates/teachers/login.html`; audit for `reverse('teachers:login')` or `/teacher/login/` remnants
- [ ] 5.5 Verify the login flow manually: (Given seeded teacher credentials, When logging in on the allauth login page, Then the teacher reaches the dashboard; When logging in with staff credentials, Then redirect to the admin site; When logging out from the panel, Then return to the login page; When requesting a password reset, Then console email output shows reset instructions)

## 6. Panel navigation menu

- [ ] 6.1 Replace the bare `<nav>` in `src/teachers/templates/teachers/base.html` with the navigation-menu component: Spanish labels, user name, panel destinations, logout as POST form (`hx-boost="false"`), keeping `django_htmx` tags and CSRF `hx-headers` intact
- [ ] 6.2 Verify: navigation renders on every panel page for a logged-in teacher, absent for anonymous users (Given an anonymous visitor, When opening the login page, Then no panel navigation renders)

## 7. Final verification

- [ ] 7.1 `uv run manage.py check` passes
- [ ] 7.2 Byte-diff harness passes on pages not styled by this change (dashboard/course/session fragments unchanged where expected; login/nav pages excluded as intentionally changed)
- [ ] 7.3 `uv run manage.py tailwind build` succeeds; no `package.json` exists in the repo
- [ ] 7.4 Grep audit: no Alpine/HTMX CDN references, no `/teacher/login/` references, shadcn components not referenced in admin templates
