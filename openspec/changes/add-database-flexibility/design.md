# Design: add-database-flexibility

## Context

`src/config/settings.py` hardcodes everything: an insecure `SECRET_KEY`, `DEBUG = True`, empty `ALLOWED_HOSTS`, and SQLite at `BASE_DIR / 'db.sqlite3'`. No environment variables are read anywhere. The project is uv-managed, has no Docker files, and `.gitignore` covers only Python artifacts and `db.sqlite3`. All models use app-side UUIDv7 primary keys (`uuid6`), so there are no AutoField sequences — data is portable across engines with plain `dumpdata`/`loaddata`. Models use only portable field types (no Postgres-specific fields).

## Goals / Non-Goals

**Goals:**

- Settings read from environment (+ optional `.env`) with dev defaults, so bare `uv run manage.py runserver` behaves exactly as today.
- `DATABASE_URL` selects the engine: unset → SQLite (default), Postgres URL → PostgreSQL via psycopg 3.
- `compose.yaml` with a single Postgres service for those who want it.
- Existing tests pass under both engines.

**Non-Goals:**

- No production deployment stack (web Dockerfile, WSGI server, static/media hosting, backups).
- No engines beyond SQLite/PostgreSQL; no django-storages.
- No automatic data migration between engines; no CI matrix.

## Decisions

### D1: `django-environ` for env access

`environ.Env(DEBUG=(bool, True), ...)` reads environment variables with typed defaults; `environ.Env.read_env()` loads a `.env` file at BASE_DIR when present. Its `env.db()` parses `DATABASE_URL` directly into a Django `DATABASES` dict — the loader and the switch are one library. Alternatives rejected: `python-dotenv` (loading only — we'd hand-roll parsing of `DATABASE_URL` and type casting), raw `os.environ` (no `.env` support; dev UX of exporting vars in every shell is poor).

### D2: `DATABASE_URL` switch, SQLite fallback

`DATABASES = {'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')}`. Unset → SQLite exactly as today; Postgres URL → engine `django.db.backends.postgresql` (psycopg 3 backend name) with host/port/creds from the URL. Alternatives rejected: discrete `DB_ENGINE`/`DB_HOST`/... vars (more knobs, less standard); making SQLite also expressible via URL only (the default already covers it).

### D3: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` env-provided with dev defaults

Defaults preserve today's behavior: `DEBUG=True`, `ALLOWED_HOSTS=[]`, and the current insecure key for local dev — documented in `.env.example` as MUST-set-for-production. This keeps the change non-breaking while establishing the env convention once, instead of introducing it piecemeal later.

### D4: `psycopg[binary]` v3 as an unconditional dependency

Django 6's `django.db.backends.postgresql` uses psycopg 3 when available. Unconditional install (vs an optional uv extra) keeps one sync path; SQLite-only devs simply never import it. Binary wheels avoid a local libpq build.

### D5: Single-service `compose.yaml`, no profiles

Service `db`: `postgres:17`, `POSTGRES_USER/PASSWORD/DB` and the published port sourced from `.env` via compose's built-in variable substitution (compose reads `.env` in the same directory automatically), named volume for data, `pg_isready` healthcheck. No profiles, no web service — "not wanting Postgres" = never running `docker compose up`. The `.env.example` ships matching `DATABASE_URL`/`POSTGRES_*` values so compose and Django point at the same database by construction.

### D6: Verification = existing test suite under both engines

No CI matrix. During implementation, run `uv run manage.py check` + tests with no `DATABASE_URL` (SQLite) and with the compose Postgres URL. Portability is structural (D2's ORM-only access, UUIDv7 PKs), not spec'd behavior.

## Risks / Trade-offs

- [Committed `.env` leaks secrets] → `.gitignore` gains `.env`; `.env.example` carries placeholders only.
- [Dev default keeps an insecure `SECRET_KEY`] → acceptable only while `DEBUG=True` local default exists; `.env.example` marks production overrides; no deploy target exists yet.
- [Engine drift — code works on SQLite, breaks on Postgres] → no engine-specific SQL anywhere; tests run on both during this change; UUIDv7 PKs remove sequence pitfalls.
- [`psycopg` installed but unused for SQLite users] → accepted (small binary wheel; single dependency set beats optional-extras friction).

## Migration Plan

Additive settings/config change; no schema or application changes. Rollback: revert `settings.py`, delete `compose.yaml`/`.env.example`. Existing SQLite dev databases keep working untouched.

## Open Questions

- None — decisions settled during exploration.
