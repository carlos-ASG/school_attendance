## Why

Settings are fully hardcoded (SECRET_KEY, DEBUG, sqlite path), which blocks production deployment and forces PostgreSQL adoption rather than allowing it. Devs who want zero setup keep SQLite; deployments that need Postgres get it via one env var and a compose file.

## What Changes

- Introduce `django-environ`; settings read from environment with a git-ignored `.env` file and sane dev defaults (bare `uv run manage.py runserver` keeps working with no `.env`).
- Move `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` to env-provided values with dev defaults.
- Database selection via `DATABASE_URL`: unset → SQLite at `db.sqlite3` (unchanged default); a Postgres URL (e.g. `postgres://...`) → psycopg 3 connection.
- Add `psycopg[binary]` v3 as a dependency (required only when Postgres is selected).
- Add `compose.yaml` with a single `postgres` service (port, volume, healthcheck, credentials from `.env`); no other services, no compose profiles — not wanting Postgres means simply never running it.
- Add `.env.example` documenting every variable; `.gitignore` ignores `.env`.

## Capabilities

### New Capabilities

- `environment-configuration`: env-based settings loading (`.env` + environment variables with dev defaults) and dual SQLite/PostgreSQL database selection via `DATABASE_URL`, plus the Postgres-only compose file.

### Modified Capabilities

<!-- None: no existing spec-level behavior changes. -->

## Impact

- `src/config/settings.py`: rewritten top section (env loading, DATABASES switch).
- New files: `compose.yaml`, `.env.example`.
- `pyproject.toml`: `django-environ`, `psycopg[binary]`.
- `.gitignore`: `.env`.
- No model/schema/migration changes; existing tests must pass under both engines.
- UUIDv7 primary keys (app-side) mean data moves between engines with plain `dumpdata`/`loaddata`.

## Non-goals

- No production deployment setup (gunicorn/uvicorn, web Dockerfile, static/media hosting, S3 storage, backups, CI matrix over both DBs).
- No django-storages or DATABASE_URL support for engines other than SQLite/PostgreSQL.
- No automatic data migration between engines (documented manual `dumpdata`/`loaddata` flow at most).
- No changes to application behavior, models, or admin.
