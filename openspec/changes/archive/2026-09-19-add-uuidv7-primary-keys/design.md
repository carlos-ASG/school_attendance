# Design: UUID v7 Primary Keys

## Context

All 10 `school` models use Django's implicit `BigAutoField` PKs (migrations `0001`–`0008`, SQLite dev DB seeded via `seed_dev_data`). `django.contrib.auth`'s `User` is used directly (`Teacher.user` OneToOne, allauth, admin). Python 3.12 has no stdlib `uuid.uuid7` (added in 3.14). Integer ids also leak into public surfaces: teacher panel URLs (`<int:pk>`), the attendance JSON API (path param + payload/response ids), and student import/export (`id` column). The project is pre-production; the dev database is disposable.

## Goals / Non-Goals

**Goals:**

- Every project model gets a UUID v7 primary key, generated client-side by Django (`default=uuid7`).
- The auth `User` model becomes a custom model with a UUID v7 PK without breaking allauth login, admin, or `Teacher.user`.
- The teacher panel, attendance API, and student import/export all speak UUID ids consistently.
- Clean migration history: regenerate `0001` migrations; reseed dev data.

**Non-Goals:**

- Data-preserving migration from integer PKs (see D4).
- UUID PKs on framework tables (sessions, contenttypes, groups, permissions, allauth tables, admin `LogEntry`).
- API versioning for the id-format break.
- Swapping generators later (`uuid-utils`, stdlib `uuid.uuid7`).

## Decisions

- **D1 — Generator: `uuid6` package.** Python 3.12 stdlib lacks `uuid7`; `uuid6` is pure Python (no native wheel concerns) and exposes `from uuid6 import uuid7` as a plain callable, ideal as a field `default`. Alternatives: `uuid-utils` (Rust, faster, but native wheel) rejected per stakeholder choice; stdlib `uuid.uuid7` requires Python ≥3.14.
- **D2 — Abstract base `UUIDv7Model` for school models.** `src/school/models/base.py` defines `id = models.UUIDField(primary_key=True, default=uuid7, editable=False)` on an abstract `models.Model`. All 10 concrete models inherit it. Alternatives: repeating the field per model (DRY violation) or a custom `UUIDv7Field` subclass (more machinery, no benefit — the default is the only difference). `accounts.User` cannot reuse the base (it must extend `AbstractUser`) and declares the same field explicitly.
- **D3 — Custom user app: new `accounts` app.** `User(AbstractUser)` with the UUID v7 pk; `AUTH_USER_MODEL = 'accounts.User'`; app added to `INSTALLED_APPS` and to `pyproject.toml` `[tool.uv.build-backend] module-name`. A dedicated app keeps auth concerns out of `school`/`teachers`. Because it is declared before the first `migrate`, all auth/allauth/admin-log tables are built against it natively — no `swappable` migration gymnastics. `ACCOUNT_LOGIN_METHODS = {'username'}` keeps working (`username` field inherited).
- **D4 — Adoption by reset, not data migration.** SQLite cannot alter column types in place; converting int PKs + remapping every FK in a data migration is high-effort, high-risk for disposable dev data. Instead: delete `db.sqlite3` and `school/migrations/000[1-8]*.py`, regenerate a clean `0001` for `accounts` and `school`, run `seed_dev_data`. Rollback = `git checkout` of migrations + DB rebuild.
- **D5 — Storage: Django `UUIDField` as-is.** On SQLite this is `char(32)`. UUID v7's time-ordered prefix gives better B-tree locality than v4 random ids; no DB-native uuid functions are needed since Django generates defaults client-side.
- **D6 — API ids become UUIDs end-to-end.** `session_id: uuid.UUID` path parameter; `id: UUID` in `AttendanceRecordIn`/`AttendanceRecordOut`/`RecordError`. Malformed ids fail schema validation (HTTP 422); well-formed-but-nonexistent session ids still return 404 per spec. API tests switch `from django.contrib.auth.models import User` to `get_user_model()` and integer stand-ins (`pk=99999`, `{'id': 99999}`) to `uuid.uuid4()` values.
- **D7 — Panel URLs use the `uuid` converter.** All six `<int:pk>` routes in `src/teachers/urls.py` become `<uuid:pk>`; views keep using `get_object_or_404`/ORM unchanged. Old integer bookmarks simply stop matching (dev-only concern). Admin URLs already treat object ids as opaque strings and `AttendanceRecordInline.get_session` already guards `ValueError` on lookup.
- **D8 — Import/export widget parses UUIDs.** `NullableIdWidget.clean` returns `UUID(value)` instead of `int(value)`; blank still maps to `None` (row creates a new Student, which receives a fresh uuid7). Exported ids are UUID strings, so a full export→import round trip still updates in place.

## Risks / Trade-offs

- **[Breaking API contract]** Consumers sending integer ids get 422s. → No external consumers exist; frontend templates/builders are updated in the same change and verified by the API test suite.
- **[`uuid6` is slower than Rust-based alternatives]** Generation is pure Python per object. → Dev-scale row counts make this negligible; the callable can be swapped centrally in `base.py`/`accounts.User` later.
- **[Test discovery for the new app]** `config.test_runner.SrcLayoutDiscoverRunner` must pick up `accounts/tests.py`. → Verify with `uv run manage.py test`; the runner already handles `src`-layout apps generically.
- **[Missed integer-PK assumption]** Some code path may still assume ints (e.g., templates building URLs manually). → Grep sweep for `<int:`, `: int` on ids, `pk=` literals; run the full test suite plus seeded smoke test of admin + panel + API.
- **[Dev data loss]** DB reset wipes local data including the `admin` superuser. → `seed_dev_data` recreates all of it; documented in tasks as an explicit step.

## Migration Plan

1. `uv add uuid6`; update `pyproject.toml` module list; settings (`INSTALLED_APPS`, `AUTH_USER_MODEL`).
2. Add `accounts` app (`User`, admin, apps, migrations package) and `school/models/base.py`; rewire all models; update URLs, API schemas, resources, tests.
3. Delete `db.sqlite3` and `src/school/migrations/000[1-8]*.py`.
4. `uv run manage.py makemigrations accounts school` → review generated `0001`s.
5. `uv run manage.py migrate && uv run manage.py seed_dev_data`.
6. `uv run manage.py check && uv run manage.py test`; smoke-test admin CRUD, teacher panel session flow, API docs.

Rollback: revert the commit; restore `db.sqlite3` from before step 3 (or reseed).

## Open Questions

None — scope (custom User included), library (`uuid6`), and reset strategy were confirmed with the stakeholder.
