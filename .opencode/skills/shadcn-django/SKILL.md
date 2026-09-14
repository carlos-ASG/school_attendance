---
name: shadcn-django
description: Use when building or styling UI with shadcn/django — running the shadcn_django CLI (init/list/add, "add component"), using components (button, card, input, label, checkbox, alert, badge, separator, navigation menu, toast, dialog, dropdown menu, select, table, tabs, sheet, popover, tooltip-like, form, textarea, progress, command), Tailwind CSS or Alpine.js setup, theming via CSS variables, or the django-allauth login block. Triggers on "shadcn", "shadcn/django", UI styling for the teacher panel.
license: MIT
---

# shadcn/django (design system)

Unofficial Django port of shadcn/ui. Components are built with Tailwind CSS and
Alpine.js, HTMX-compatible, and rendered through django-cotton (`<c-button>`, …).
The cotton layer itself is covered by the `django-cotton` skill — load both.
Docs: https://shadcn-django.com

## Philosophy: not a library — you own the code

`uvx shadcn_django@latest add <component>` copies component source (+ its
dependencies) into `templates/cotton/`. Nothing is a runtime dependency. Editing the
copied files is expected and normal: translating copy to Spanish, tweaking classes,
adding variants. Component changes are made in your repo, not upstream.

**Repo location:** components live in `src/core_ui/templates/cotton/` (the `core_ui`
design-system app). The CLI always writes to project-root `templates/cotton/` — after
`add`, move the new files into `src/core_ui/templates/cotton/` (cotton 2.7.2 discovers
`<app>/templates/` dirs of every installed app, so no loader config is needed).

## Install flow (this repo's decisions)

1. **django-cotton first** — `uv add django-cotton` + `INSTALLED_APPS` (see
   `django-cotton` skill).
2. **Scaffold** — `uvx shadcn_django@latest init` from the repo root. Creates
   `templates/cotton/`, an `input.css`, and the shadcn CSS variables (design tokens).
   Move both into the `core_ui` app (`src/core_ui/templates/cotton/`,
   `src/core_ui/input.css`), then delete the project-root leftovers. Inspect the
   resulting diff and reconcile with existing settings (it may write config files);
   verify with `uv run manage.py check`.
3. **Tailwind build — django-tailwind-cli** (repo stays uv-only, no node):
   - `uv add django-tailwind-cli`, add `django_tailwind_cli` to `INSTALLED_APPS`
   - `uv run manage.py tailwind install_cli` (downloads the tailwind CLI binary)
   - `uv run manage.py tailwind start` (watch mode alongside `runserver`;
     `tailwind build` for a one-off)
   - `tw-animate-css` (shadcn animations) is installed via the manual CSS download —
     no npm. Verify exact input/output paths and settings against
     https://github.com/donkz/django-tailwind-cli docs during implementation.
4. **Alpine.js — vendor it** like `src/teachers/static/teachers/js/htmx.min.js`:
   download `alpine.min.js` (3.x CDN build) into static and load with
   `<script defer src="...">` in `<head>`. No CDN in templates.
5. **Base template `<head>`**: link the compiled CSS (`core-ui/css/output.css`) +
   Alpine script (`core-ui/js/alpine.min.js`), both served from the `core_ui` app's
   static dir (`src/core_ui/static/core-ui/`); no `TEMPLATES[0]['DIRS']` needed —
   app template dirs are discovered natively.

## CLI

```bash
uvx shadcn_django@latest --help
uvx shadcn_django@latest list              # available components
uvx shadcn_django@latest add button        # one component + deps
uvx shadcn_django@latest add navigation_menu toast   # several
```

Components land in `templates/cotton/` — inspect filenames after `add` to confirm
they match the repo's default snake_case expectations (`COTTON_SNAKE_CASED_NAMES = True`),
then move them into `src/core_ui/templates/cotton/`.

## Component catalog

Accordion · Alert · Alert Dialog · Badge · Button · Card · Checkbox · Combobox ·
Command · Command Dialog · Dialog · Dropdown Menu · Form · Input · Label ·
Navigation Menu · Popover · Progress · Select · Separator · Sheet · Table · Tabs ·
Textarea · Toast — each at `https://shadcn-django.com/<name>` (underscores).

## Usage patterns

```html
<c-button>Default</c-button>
<c-button variant="outline">Cancel</c-button>
<c-button class="w-full mt-4">Extra classes merge</c-button>
```

Compound components use dot notation: `c-card.header`, `c-card.title`,
`c-card.description`, `c-card.content`, `c-card.footer`; forms pair `c-label`
+ `c-input` (+ `c-checkbox`); icons are inline SVG or `cotton-icons` components.

Navigation Menu (Alpine-powered dropdown nav for the teacher panel):

```html
<c-navigation-menu>
    <c-navigation-menu.list>
        <c-navigation-menu.item>
            <c-navigation-menu.trigger index='0'>Asistencia</c-navigation-menu.trigger>
            <c-navigation-menu.content index='0'>
                <c-navigation-menu.link href='/teacher/'>Panel</c-navigation-menu.link>
            </c-navigation-menu.content>
        </c-navigation-menu.item>
        <c-navigation-menu.item>
            <c-navigation-menu.link href='…'>Enlace simple</c-navigation-menu.link>
        </c-navigation-menu.item>
    </c-navigation-menu.list>
</c-navigation-menu>
```

`trigger`/`content` pairs are matched by `index`. Toasts: `<c-toast.trigger
toast_target="id">` + `<c-toast id="id"><c-toast.content type=… title=… …/></c-toast>`.
HTMX attrs pass through via `{{ attrs }}` (cotton skill).

## django-allauth block (login — chosen approach)

`uvx shadcn_django@latest add allauth` installs **17 templates** to
`templates/account/` plus the components they use (Card, Button, Input, Label,
Checkbox, Alert, Badge, Separator) — in this repo the block lives in
`src/core_ui/templates/account/` (+ `base.html`) and `core_ui` precedes `allauth`
in `INSTALLED_APPS` so the copies shadow allauth's builtins:

- Auth: `login.html`, `signup.html`, `logout.html`, `reauthenticate.html`
- Password: `password_change.html`, `password_set.html`, `password_reset.html`,
  `password_reset_done.html`, `password_reset_from_key.html`,
  `password_reset_from_key_done.html`
- Email: `email.html`, `email_change.html`, `email_confirm.html`,
  `verification_sent.html`, `verified_email_required.html`
- Status: `account_inactive.html`, `signup_closed.html`

Repo config (replace the current `django.contrib.auth` LoginView wiring):

```python
uv add django-allauth
INSTALLED_APPS  += ['allauth', 'allauth.account']
MIDDLEWARE     += ['allauth.account.middleware.AccountMiddleware']
AUTHENTICATION_BACKENDS = [
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]
ACCOUNT_LOGIN_METHODS = {'username'}      # keep username login — seeded teacher accounts use it
ACCOUNT_EMAIL_VERIFICATION = 'optional'   # dev: console email backend (MAILERS)
LOGIN_URL = 'account_login'               # replace '/teacher/login/'
```

- Templates live app-level (`src/core_ui/templates/account/`); no `TEMPLATES[0]['DIRS']`
  — `core_ui` must appear before `allauth` in `INSTALLED_APPS`.
- Signup is closed by business rule (accounts created via django-admin): the adapter
  returns `False` from `is_open_for_signup()` and the login page has no signup link;
  templates are kept for potential future use.
- Verify django-allauth resolves against **Django 6.1** on the first
  `uv add django-allauth`; confirm with `uv run manage.py check` + migrations.
- The staff→admin / teacher→dashboard redirect logic from
  `src/teachers/views/auth.py` moves to allauth's `ACCOUNT_LOGIN_REDIRECT_URL` (or a
  custom adapter) — don't lose it.
- Shipped copy is English → translate to Spanish after adding (you own the code):
  Sign In → Iniciar sesión, Password → Contraseña, Remember me → Recordarme,
  Sign Up → Registrarse, Forgot Password? → ¿Olvidaste tu contraseña?,
  Sign Out → Cerrar sesión, Email → Correo electrónico.

## Boundaries (repo rules)

- **Unfold owns `/admin/`** (theme + `src/school/components.py` charts). shadcn/django
  owns the teacher panel front-end. Never mix: no shadcn components in admin, no
  unfold components in the panel.
- Spanish UI copy everywhere.
- HTMX fragments follow the `django6-htmx` skill (`partialdef`); cotton components
  may be used inside fragments; `render_component()` only for single-component responses.

## References

- Intro/install: https://shadcn-django.com/ · https://shadcn-django.com/installation/
- Full install guide: https://github.com/SarthakJariwala/shadcn-django (README)
- Blocks: https://shadcn-django.com/allauth/
- Alpine.js: https://alpinejs.dev/ · tw-animate-css manual install:
  https://github.com/wombosvideo/tw-animate-css
- django-tailwind-cli: https://github.com/donkz/django-tailwind-cli
