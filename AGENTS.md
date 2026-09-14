# AGENTS.md

## Commands

- Package/env is managed by `uv` (Python >= 3.12). Always run Django via `uv run manage.py <command>` (e.g. `uv run manage.py check`, `uv run manage.py migrate`, `uv run manage.py runserver`).
- No test suite, linter, or CI yet. Minimum verification after changes: `uv run manage.py check`.

## Layout quirks

- `manage.py` stays at the repo root; it works because `uv run` installs the project (editable) — always use `uv run manage.py <command>`, not bare `python manage.py`.
- Django settings module is `config.settings` — the project package is `src/config/` (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`).
- Django apps live in `src/` (e.g. `src/school/`); `uv_build` packages them via `module-name = ["config", "school"]` in `pyproject.toml` — add new top-level app packages to that list.
- `INSTALLED_APPS` includes the `school` app (models for the attendance domain) and the
  `core_ui` app — the design system (django-cotton components in `src/core_ui/templates/cotton/`,
  the shadcn/allauth template block in `src/core_ui/templates/account/`, and the Tailwind assets
  namespaced `core-ui/` under `src/core_ui/static/`; input CSS at `src/core_ui/input.css`). Database is SQLite
  (`db.sqlite3` at repo root).
- Email is configured via a `MAILERS` setting with console backend (dev only).

## OpenSpec workflow

- This repo uses OpenSpec (spec-driven development); see `openspec/` and the `openspec-*` skills (`.opencode/skills/`) for propose/apply/archive flows. Use those skills instead of ad-hoc feature work; specs live in `openspec/specs/`, active changes in `openspec/changes/`.

## Skill Invocation Guidelines

Agents should proactively load the repository skill that matches the task before making changes, reviewing code, or generating output. Do not wait for the user to explicitly ask for the skill when the task clearly matches one of these cases.

| Task or Trigger | Required Skill | When To Use |
|-----------------|----------------|-------------|
| Exploring ideas, investigating a problem, clarifying requirements before writing a change | `openspec-explore` | Use when the user wants to think through something (brainstorm, trade-offs, unknowns) before or during a change. |
| New feature, behavior change, or bug fix with user-visible effects | `openspec-propose` | Use before any ad-hoc feature work: creates the change and all artifacts (proposal, design, specs, tasks) in one step. |
| Implementing tasks from an active change in `openspec/changes/` | `openspec-apply-change` | Use when starting or continuing implementation; read the change artifacts, work through tasks, tick checkboxes as you go. |
| Change implementation is complete and verified | `openspec-archive-change` | Use to finalize: validates deltas, syncs main specs (use `--skip-specs` for no-delta refactors), archives the change. |
| Updating main specs with delta specs without archiving | `openspec-sync-specs` | Use only when the user wants specs synced mid-change. |
| Django 6 + HTMX work: template partials (`{% partialdef %}`, `{% partial %}`, `render('page.html#partial_name')`), HTMX fragment endpoints, `hx-*` attributes, django-htmx, template/fragment restructuring, flat template layout | `django6-htmx` | Use when creating, changing, or reviewing HTMX views, templates, or fragments — and when verifying template refactors with the byte-diff harness. |
| django-cotton component work: `templates/cotton/`, `<c-...>` tags, `{% cotton %}`, slots, `c-vars`, variants, attribute proxying, compound components, cotton/Alpine interop | `django-cotton` | Use when writing or editing cotton components or using `<c-*>` tags in templates. |
| shadcn/django UI work: `shadcn_django` CLI (`uvx shadcn_django@latest add ...`), shadcn components (button, card, input, navigation menu, toast, ...), Tailwind/Alpine setup, theming CSS variables, django-allauth login templates, teacher-panel styling | `shadcn-django` | Use for design-system/UI styling work; co-load `django-cotton` (and `django6-htmx` when fragments are involved). |

When multiple skills apply, load all relevant skills. For example, implementing a new HTMX fragment endpoint as part of an active change should load `openspec-apply-change` and `django6-htmx`; proposing a feature that touches HTMX templates should load `openspec-propose` and `django6-htmx`; building a styled teacher-panel UI with components should load `shadcn-django` and `django-cotton`.
