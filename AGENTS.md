# AGENTS.md

## Commands

- Package/env is managed by `uv` (Python >= 3.12). Always run Django via `uv run manage.py <command>` (e.g. `uv run manage.py check`, `uv run manage.py migrate`, `uv run manage.py runserver`).
- No test suite, linter, or CI yet. Minimum verification after changes: `uv run manage.py check`.

## Layout quirks

- `manage.py` stays at the repo root; it works because `uv run` installs the project (editable) — always use `uv run manage.py <command>`, not bare `python manage.py`.
- Django settings module is `config.settings` — the project package is `src/config/` (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`).
- Django apps live in `src/` (e.g. `src/school/`); `uv_build` packages them via `module-name = ["config", "school"]` in `pyproject.toml` — add new top-level app packages to that list.
- `INSTALLED_APPS` includes the `school` app (models for the attendance domain). Database is SQLite (`db.sqlite3` at repo root).
- Email is configured via a `MAILERS` setting with console backend (dev only).

## OpenSpec workflow

- This repo uses OpenSpec (spec-driven development); see `openspec/` and the `openspec-*` skills (`.opencode/skills/`) for propose/apply/archive flows. Use those skills instead of ad-hoc feature work; specs live in `openspec/specs/`, active changes in `openspec/changes/`.
