---
name: django-cotton
description: Use when authoring or editing django-cotton components (templates/cotton/, <c-* tags, {% cotton %}, c-vars, c-slot, named slots, attrs, variants, compound components) or wiring them into Django templates in this repo. Covers cotton setup, the full syntax reference, Alpine.js interop, and the coexistence rules with Django 6 partialdef HTMX fragments.
license: MIT
---

# django-cotton

Cotton is this repo's UI component engine — the layer under shadcn/django (see the
`shadcn-django` skill for the design system and CLI). Run all Django commands via
`uv run manage.py <cmd>`.

## Setup (this repo)

- Dependency: `uv add django-cotton`. Version support: Django >4.2,<7.0 (6.1 OK), Python >=3.8,<4.
- `INSTALLED_APPS = [..., 'django_cotton', ...]` — **automatic configuration** injects
  the cotton loader chain and the `cotton` templatetag builtins into `TEMPLATES`
  (cached.Loader included automatically). Do not hand-edit `OPTIONS['loaders']`
  unless something forces manual setup; if so, switch to
  `django_cotton.apps.SimpleAppConfig` and copy the explicit loader/builtins config
  from the quickstart docs.
- Components live at project root: `<repo>/templates/cotton/` (`BASE_DIR` is the repo
  root). Regular templates placed next to them (e.g. `templates/account/`) require
  `TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']` — currently `DIRS: []` in
  `src/config/settings.py`.

## Naming and location rules

- Filenames are snake_case by default: `<c-my-component />` → `cotton/my_component.html`.
  kebab-case filenames need `COTTON_SNAKE_CASED_NAMES = False` (not the repo default).
- Dot notation = folders: `<c-card.header />` → `cotton/card/header.html`.
- `index.html` in a folder makes the folder itself the default component: `cotton/card/index.html`
  → `<c-card />`, siblings via `<c-card.header />` (compound components).
- Config keys (`src/config/settings.py`): `COTTON_DIR` (default `'cotton'`),
  `COTTON_BASE_DIR` (None → `BASE_DIR`), `COTTON_SNAKE_CASED_NAMES` (True),
  `COTTON_ISOLATE_BY_DEFAULT` (False).

## Syntax reference

| Concept | HTML-like (preferred) | Native DTL |
|---|---|---|
| Component | `<c-button>…</c-button>` | `{% cotton button %}…{% endcotton %}` |
| Self-closing | `<c-button />` | `{% cotton button / %}` |
| Vars | `<c-vars title />` | `{% cotton:vars title %}` |
| Named slot | `<c-slot name="header">…</c-slot>` | `{% cotton:slot header %}…{% endcotton:slot %}` |

- **`{{ slot }}`** — everything between the component's opening and closing tags.
- **Named slots** — `<c-slot name="icon">…</c-slot>` in the caller, rendered inside
  the component as `{{ icon }}`. Can contain HTML or any Django template expression.
- **Attributes** are strings by default. Dynamic values:
  - quoteless for simple literals/variables: `enabled=True`, `start=42`, `value=my_variable`
  - colon prefix for anything with spaces/quotes or complex types:
    `:options="['yes','no']"`, `:config="{'open': True}"`, `:today="today"`
- **`{{ attrs }}`** — prints all received attributes (except keys declared in
  `<c-vars />`) as HTML attributes. Primary passthrough for form elements and `hx-*`.
- **`:attrs="widget_attrs"`** — merges a dict from context into attrs;
  `:attrs="attrs"` inside a wrapper component proxies all attributes to an inner
  component with types preserved (higher-order component pattern).
- **`<c-vars />`** — local defaults / component state; declared keys are excluded
  from `{{ attrs }}`. Example: `<c-vars type="text" errors leading_icon />`.
- **Boolean attributes** — bare attribute name → True: `<c-input name="x" required />`.
- **Dynamic components** — `<c-component is="icons.{{ icon_name }}" />` or `:is="variable"`.
- **Context**: components inherit parent context by default. `only` attribute = full
  isolation (blocks context processors too). `COTTON_ISOLATE_BY_DEFAULT = True` =
  smart isolation (blocks parent template vars, keeps `request`/`user`/`messages`).

## Variants pattern

Named styling options in one file via a `:variants` map + `get_item` filter:

```django
<c-vars
    variant="default"
    :variants="{
        'default': 'bg-gray-200 text-gray-800 hover:bg-gray-300',
        'primary': 'bg-sky-500 text-white hover:bg-sky-600',
        'danger': 'bg-red-500 text-white hover:bg-red-600',
    }"
/>

<button {{ attrs }} class="px-4 py-2 rounded {{ variants|get_item:variant }}">
    {{ slot }}
</button>
```

- The variants map lives in `c-vars` → never leaks into rendered HTML.
- Always provide a `default`; use intent names (`info`/`success`/`warning`/`danger`),
  not colour names. Multiple maps for orthogonal options (e.g. `:outlined-variants`).

## Form input pattern

```django
{# cotton/field.html #}
<c-vars type="text" errors label leading_icon />
{% if label %}<label>{{ label }}</label>{% endif %}
<div class="...">
    {% if leading_icon %}<div>{{ leading_icon }}</div>{% endif %}
    <input type="{{ type }}" {{ attrs }} class="... {% if errors %}border-red-500{% endif %}">
</div>
{% if errors %}{% for error in errors %}<p class="text-red-500">{{ error }}</p>{% endfor %}{% endif %}
```

Usage: `<c-field name="surname" placeholder="Surname" :errors="form.surname.errors" />`
with `<c-slot name="leading_icon"><svg>…</svg></c-slot>` for icons.

## Alpine.js interop

- `x-data` is accessible as `{{ x_data }}` (cotton generates snake_case versions of
  kebab-cased attributes); using `{{ attrs }}` already outputs the correct case.
- Alpine `:bind` shorthand conflicts with cotton's `:` dynamic-attr prefix — escape
  with `::` so a single colon survives into `{{ attrs }}`.
- Register reusable Alpine data once (`document.addEventListener('alpine:init', …)`
  with `Alpine.data('tabs', …)`) — e.g. in the base template; components reference
  it via `x-data="tabs"`.

## Layouts (available pattern)

Cotton layouts are components: `cotton/layouts/base.html` wraps `{{ slot }}`;
variants (`guest.html`, `app.html` with a `sidebar` named slot) wrap the base.
`teachers/base.html` currently uses `{% extends %}` — keep `{% extends %}` for page
chrome unless a change decides otherwise; if you migrate, verify with the byte-diff
harness (`django6-htmx` skill).

## HTMX coexistence (repo rules)

- **Django 6 `{% partialdef %}` fragments stay the mechanism for page-specific HTMX
  endpoints** — see the `django6-htmx` skill. Do not migrate existing fragments to cotton.
- Cotton components compose fine *inside* partialdef fragments.
- `render_component(request, "component-name", **context)` (`from django_cotton`) may
  return a single component as an HTMX response — use **only when the whole response
  is one component**. Otherwise render `page.html#partial` as usual.
- Pass `hx-*` attributes through components via `{{ attrs }}`:
  `<c-button hx-post="/follow" hx-swap="outerHTML">Follow</c-button>`.
- CSRF: `hx-headers='{"x-csrftoken": "{{ csrf_token }}"}'` stays on `<body>` in base.html.

## Naming collision warning

`src/school/components.py` registers **unfold admin chart components**
(`LineChartComponent`, `BarChartComponent`, `PieChartComponent`) — unrelated to
cotton components. "Components" in a templates context = cotton; in
`src/school/components.py` = unfold admin. Don't conflate or "fix" the wrong one.

## Language

UI copy is Spanish (`LANGUAGE_CODE = 'es'`). Write Spanish when creating or editing
component content/default copy.

## References

- Docs (all read; sections): https://django-cotton.com/docs/quickstart · /components ·
  /fundamentals · /configuration · /thinking-in-components · /form-fields · /alpine-js ·
  /layouts · /icons · /variants · /attribute-proxying · /index-component · /htmx-examples
- Icons as components: `cotton-icons` (Heroicons/Tabler/Lucide) — https://pypi.org/project/cotton-icons/
- PyPI: https://pypi.org/project/django-cotton/
