# UI Components Specification

## Purpose

Define the component-based design system for the teacher panel front-end, covering cotton components, shadcn/django components, Tailwind CSS build, Alpine.js, admin isolation, and HTMX fragment compatibility.

## Requirements

### Requirement: Component-based UI system
The teacher panel front-end SHALL be built with django-cotton components: reusable components SHALL live in `src/core_ui/templates/cotton/` inside the dedicated `core_ui` app and be used from templates as `<c-*>` tags (slots, `<c-vars />`, variants). The `core_ui` app SHALL own the design-system templates and statics so they are reusable by future apps (e.g. a students panel). User-visible component copy SHALL be in Spanish.

#### Scenario: Panel template uses a design-system component
- **WHEN** a panel template includes a design-system component such as `<c-button variant="outline">Cancelar</c-button>`
- **THEN** the component renders with its Tailwind styles and the provided content, with no extra wiring

#### Scenario: Custom component authored in-repo
- **WHEN** a developer creates `templates/cotton/<name>.html` using slots, `<c-vars />` defaults, or a variants map
- **THEN** the component is usable as `<c-name />` (or `<c-name.<part> />` for compound folders) without registering anything in Python

### Requirement: Design-system components are owned in-repo
shadcn/django components SHALL be added to the repo via the `shadcn_django` CLI (`uvx shadcn_django@latest add <component>`), which copies component source and its dependencies into `templates/cotton/`. The copied code SHALL be maintained in the repo — edited, extended, and translated to Spanish — rather than consumed as a runtime dependency.

#### Scenario: A component is added via the CLI
- **WHEN** `uvx shadcn_django@latest add button` is run
- **THEN** the button component source (and any dependencies it requires) is copied into the repo's cotton components directory and is committed to the repo (the CLI writes to the project-root `templates/cotton/`; files are then moved into `src/core_ui/templates/cotton/`)

#### Scenario: Signup is closed by business rule
- **WHEN** a user opens the account signup URL
- **THEN** no registration interface is reachable from the login page and the signup URL renders the sign-up-closed page (accounts are created by admins via django-admin; the `signup` templates are kept for potential future use)

#### Scenario: Shipped English copy is translated
- **WHEN** a copied component or allauth template contains user-visible English text
- **THEN** it is translated to Spanish in the repo's copy

### Requirement: Tailwind CSS built without node
The design system's styles SHALL be built with Tailwind CSS using django-tailwind-cli (uv-managed tooling, no node/npm in the repo), including the `tw-animate-css` stylesheet for component animations. The compiled CSS SHALL live in the `core_ui` app's static files (namespaced `core-ui/`) and be linked from the panel base template.

#### Scenario: Styles are rebuilt
- **WHEN** `uv run manage.py tailwind build` (or the `tailwind start` watcher) runs
- **THEN** the compiled CSS is produced into `src/core_ui/static/core-ui/css/output.css` from the design-system input CSS and is served as `core-ui/css/output.css`

#### Scenario: Repo stays uv-only
- **WHEN** the design system is installed
- **THEN** the repo requires no `package.json` or npm tooling to build styles

### Requirement: Alpine.js is vendored
Alpine.js SHALL be vendored into the project's static files and loaded via a deferred script tag in the panel base template. Templates SHALL NOT reference an Alpine CDN.

#### Scenario: Interactive components initialize offline
- **WHEN** the panel is loaded without internet access
- **THEN** Alpine-powered components (navigation menu, toasts) initialize from the vendored script

### Requirement: Unfold admin keeps its own design system
The Django admin SHALL continue to use the Unfold theme and its components (`src/school/components.py` admin charts). shadcn/django components SHALL NOT be used inside `/admin/`, and Unfold components SHALL NOT be used in the teacher panel.

#### Scenario: Admin pages are unchanged
- **WHEN** an admin user opens the Django admin site
- **THEN** pages render with the existing Unfold theme and no shadcn component code appears in admin templates

### Requirement: HTMX fragments keep the partialdef mechanism
HTMX responses in the panel SHALL keep Django 6 `{% partialdef %}` fragments as the fragment mechanism (rendered via `template_name#partial_name`). Cotton components MAY be composed inside fragments. Rendering a cotton component directly with `render_component()` SHALL be used only when the entire response is a single component. Existing fragment endpoints SHALL continue to return only their fragments.

#### Scenario: Existing fragments are unaffected by cotton
- **WHEN** the Teacher toggles a status button or saves attendance via HTMX after cotton is installed
- **THEN** the responses contain only the corresponding partialdef fragment, as before
