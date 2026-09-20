## 1. Environment loading

- [x] 1.1 Add `django-environ` and `psycopg[binary]` via `uv add`. Given the updated lockfile, when `uv run manage.py check` runs, then both packages import cleanly.
- [x] 1.2 Rework `src/config/settings.py`: `environ.Env.read_env()` at BASE_DIR; `SECRET_KEY` (current dev value as default), `DEBUG` (default `True`), `ALLOWED_HOSTS` (default `[]`) read via `environ.Env`. Given no `.env` and no exported vars, when Django starts, then behavior is identical to today.
- [x] 1.3 Replace the hardcoded `DATABASES` with `env.db('DATABASE_URL', default='sqlite:///db.sqlite3')` resolving to `BASE_DIR / 'db.sqlite3'` for the default. Given an unset `DATABASE_URL`, when `migrate` runs, then it applies to `db.sqlite3` as before.

## 2. Compose + env example

- [x] 2.1 Create `compose.yaml` with a single `db` service (`postgres:17`, `POSTGRES_USER/PASSWORD/DB` and port from `.env`, named `pgdata` volume, `pg_isready` healthcheck). Given `.env` copied from `.env.example`, when `docker compose up -d` runs, then Postgres is reachable at the published port and healthy.
- [x] 2.2 Create `.env.example` documenting `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, and the `POSTGRES_*` values, with the `DATABASE_URL` value pointing at the compose service by construction. Add `.env` to `.gitignore`.

## 3. Verification (both engines)

- [x] 3.1 Given no `DATABASE_URL`, when `uv run manage.py check` and `uv run manage.py test` run, then everything passes on SQLite.
- [x] 3.2 Given the compose Postgres from `.env.example`, when `DATABASE_URL=postgres://... uv run manage.py migrate` and `... test` run against it, then migrations apply and all tests pass on PostgreSQL.
- [x] 3.3 Manual smoke: with the Postgres URL active, run `seed_dev_data`, log into the admin, and confirm normal behavior; then `docker compose down` (no `-v`) and `up -d` and confirm the data persists.
