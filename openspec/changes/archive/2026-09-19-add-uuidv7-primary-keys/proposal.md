# Proposal: UUID v7 Primary Keys

## Why

All project models currently rely on Django's implicit auto-increment integer primary keys. Sequential integers leak record counts and ordering, and create cross-environment merge hazards (two dev databases producing colliding ids when data is later merged or synced). The project is pre-production with a resettable dev database, so now is the cheapest moment to switch the identity strategy before any data must be preserved.

## What Changes

- **BREAKING**: Every project model (`school` app: `Student`, `Teacher`, `StudentGroup`, `Subject`, `Course`, `SchoolCycle`, `NonSchoolDay`, `AttendanceSession`, `AttendanceRecord`, `ClassSchedule`) switches from implicit `BigAutoField` to UUID v7 primary keys.
- **BREAKING**: A custom `User` model is introduced in a new `accounts` app (`AbstractUser` subclass) with a UUID v7 primary key; `AUTH_USER_MODEL` points to it.
- New `uuid6` dependency provides `uuid7` (Python 3.12 stdlib has no `uuid.uuid7`).
- **BREAKING**: Attendance API ids (`session_id` path parameter, record `id` fields in request/response/error schemas) change from integers to UUID strings.
- **BREAKING**: Student import/export `id` column changes from integer to UUID string.
- Teacher panel URLs change shape from `<int:pk>` to `<uuid:pk>` (behavior unchanged).
- Dev database is reset: `db.sqlite3` deleted, `school` migrations `0001`–`0008` deleted and regenerated as a clean `0001`, dev data restored via `seed_dev_data`.

## Capabilities

### New Capabilities

- `uuid-primary-keys`: UUID v7 identity strategy for all project models, including the custom user model, and the migration-reset approach for adopting it.

### Modified Capabilities

- `attendance-api`: id fields in the bulk update endpoint (path parameter, record ids in payloads, responses, and error details) become UUID strings instead of integers.
- `student-import-export`: the `id` column in student import/export becomes UUID strings; blank ids still create new records.

## Impact

- **Models**: all 10 `school` models + new `accounts.User`; abstract `UUIDv7Model` base and explicit pk field on `User`.
- **API**: `src/api/api.py` (`session_id: UUID`), `src/api/schemas.py` (id types), consumers must send/receive UUID strings.
- **URLs**: `src/teachers/urls.py` converters, admin URLs now embed UUIDs (admin already handles string object ids).
- **Import/export**: `src/school/resources.py` `NullableIdWidget` parses UUIDs.
- **Settings/packaging**: `INSTALLED_APPS`, `AUTH_USER_MODEL`, `pyproject.toml` module list gains `accounts`; dependency `uuid6` added.
- **Data**: dev database wiped and reseeded; not deployable over existing production data (none exists).
- Framework tables (auth groups, sessions, contenttypes, allauth, admin logentry) keep their native keys; only `User` itself moves to UUID.

## Non-goals

- No data-preserving migration from integer PKs (dev DB is reset instead).
- No changing framework-managed tables (sessions, contenttypes, groups, permissions, allauth tables, admin LogEntry) to UUID PKs.
- No API versioning layer for the id-format break (no external consumers yet).
- No switching the UUID library later to `uuid-utils` or stdlib `uuid.uuid7` (Python 3.14+).
