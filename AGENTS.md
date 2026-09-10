# AGENTS.md

## Commands

- Package/env is managed by `uv` (Python >= 3.12). Always run Django via `uv run manage.py <command>` (e.g. `uv run manage.py check`, `uv run manage.py migrate`, `uv run manage.py runserver`).
- No test suite, linter, or CI yet. Minimum verification after changes: `uv run manage.py check`.

## Layout quirks

- Django settings module is `config.settings` — the project package is the root-level `config/` directory (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`), NOT `src/school_attendance/`.
- `src/school_attendance/` is only an empty placeholder required by the `uv_build` backend (`pyproject.toml`); its `school-attendance` entry point script is unused. Put Django code in root `config/` or new Django apps, not in `src/`.
- No Django apps exist yet (`INSTALLED_APPS` has only defaults). Database is SQLite (`db.sqlite3` at repo root) and no migrations exist yet — run `manage.py makemigrations` after adding models.
- Email is configured via a `MAILERS` setting with console backend (dev only).

## OpenSpec workflow

- This repo uses OpenSpec (spec-driven development); see `openspec/` and the `openspec-*` skills (`.opencode/skills/`) for propose/apply/archive flows. Use those skills instead of ad-hoc feature work; specs live in `openspec/specs/`, active changes in `openspec/changes/`.
