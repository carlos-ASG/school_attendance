# environment-configuration Specification

## Purpose

Configure Django settings through environment variables with safe development defaults, and allow the database engine to be selected via `DATABASE_URL` (SQLite by default, PostgreSQL when a Postgres URL is provided), with a Postgres-only compose file for local development.

## Requirements

### Requirement: Environment-based settings with development defaults

Settings SHALL be read from environment variables (optionally provided via a `.env` file at the project root) using `django-environ`. `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` SHALL be env-provided with defaults that reproduce the current development behavior. A `.env.example` file SHALL document every supported variable, and `.env` SHALL be git-ignored.

#### Scenario: Bare checkout works with no .env

- **WHEN** the project is run with no `.env` file and no relevant environment variables set (e.g. `uv run manage.py runserver`)
- **THEN** Django starts with `DEBUG=True`, the development `SECRET_KEY`, empty `ALLOWED_HOSTS`, and SQLite at `db.sqlite3`, identical to the pre-change behavior

#### Scenario: Environment overrides settings

- **WHEN** `SECRET_KEY`, `DEBUG=False`, and `ALLOWED_HOSTS=example.com` are set in the environment or `.env`
- **THEN** Django uses those values instead of the development defaults

#### Scenario: .env is not committed

- **WHEN** the repository is inspected
- **THEN** `.gitignore` excludes `.env` and the repo contains `.env.example` with placeholder values for every supported variable

### Requirement: Database selection via DATABASE_URL

The database engine SHALL be selected by the `DATABASE_URL` environment variable. When `DATABASE_URL` is unset, the project SHALL use SQLite at the repository root's `db.sqlite3`. When `DATABASE_URL` is a PostgreSQL URL, the project SHALL connect to PostgreSQL using the `psycopg` 3 driver with host, port, credentials, and database name taken from the URL. No application code or models SHALL depend on which engine is active.

#### Scenario: Default SQLite

- **WHEN** `DATABASE_URL` is not set
- **THEN** `migrate` applies migrations to `db.sqlite3` and all existing behavior is unchanged

#### Scenario: PostgreSQL selected

- **WHEN** `DATABASE_URL` is set to a `postgres://` URL of a reachable PostgreSQL server
- **THEN** `migrate` applies migrations to that PostgreSQL database via psycopg 3 and the application behaves identically to SQLite

#### Scenario: Test suite passes on both engines

- **WHEN** the existing test suite runs once with `DATABASE_URL` unset and once with a PostgreSQL URL
- **THEN** all tests pass in both runs

### Requirement: Postgres-only compose file

The repository SHALL include a `compose.yaml` containing exactly one service: PostgreSQL. The service credentials, database name, and published port SHALL come from `.env` variables, with a named volume for data persistence and a readiness healthcheck. The compose file SHALL NOT include any other service.

#### Scenario: Start Postgres for development

- **WHEN** the user runs `docker compose up -d` with the `.env` values copied from `.env.example`
- **THEN** a PostgreSQL server becomes reachable at the published port using the `.env` credentials, and `DATABASE_URL` in the same `.env` points at it

#### Scenario: Data survives restarts

- **WHEN** the containers are stopped with `docker compose down` (no `-v`) and later started again
- **THEN** the PostgreSQL data persisted by the named volume is still present

#### Scenario: Compose file stays Postgres-only

- **WHEN** the repository's `compose.yaml` is inspected
- **THEN** it defines only the PostgreSQL service (and its volume), with no web/app service
