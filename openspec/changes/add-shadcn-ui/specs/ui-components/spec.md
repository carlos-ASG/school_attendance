# ui-components — Spec Delta

## ADDED Requirements

### Requirement: Component-based UI system
The teacher panel front-end SHALL be built with django-cotton components: reusable components SHALL live in `templates/cotton/` at the project root and be used from templates as `<c-*>` tags (slots, `<c-vars />`, variants). The system SHALL support the project-root templates directory through `TEMPLATES[0]['DIRS']`. User-visible component copy SHALL be in Spanish.

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
- **THEN** the button component source (and any dependencies it requires) is copied into `templates/cotton/` and is committed to the repo

#### Scenario: Shipped English copy is translated
- **WHEN** a copied component or allauth template contains user-visible English text
- **THEN** it is translated to Spanish in the repo's copy

### Requirement: Tailwind CSS built without node
The design system's styles SHALL be built with Tailwind CSS using django-tailwind-cli (uv-managed tooling, no node/npm in the repo), including the `tw-animate-css` stylesheet for component animations. The compiled CSS SHALL be linked from the panel base template.

#### Scenario: Styles are rebuilt
- **WHEN** `uv run manage.py tailwind build` (or the `tailwind start` watcher) runs
- **THEN** the compiled CSS is produced from the project's templates and is served as a static file

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
