# Tasks: UUID v7 Primary Keys

## 1. Dependencies and configuration

- [x] 1.1 Add the `uuid6` dependency: `uv add uuid6`; confirm `uv.lock` updated
- [x] 1.2 Add `"accounts"` to `[tool.uv.build-backend] module-name` in `pyproject.toml`
- [x] 1.3 In `src/config/settings.py`: add `'accounts'` to `INSTALLED_APPS` (before `django.contrib.auth`) and set `AUTH_USER_MODEL = 'accounts.User'`
- [x] 1.4 Verify `uv run manage.py check` passes (it will fail later steps if config is wrong — rerun after each group)

## 2. Custom user model

- [x] 2.1 Scaffold `src/accounts/` app: `apps.py` (`AccountsConfig`), `__init__.py`, `migrations/__init__.py`
- [x] 2.2 `src/accounts/models.py`: `User(AbstractUser)` with `id = models.UUIDField(primary_key=True, default=uuid7, editable=False)` using `from uuid6 import uuid7`; keep inherited fields untouched
- [x] 2.3 `src/accounts/admin.py`: register `User` with Unfold `ModelAdmin` (`list_display` covering username/staff flags)
- [x] 2.4 `src/accounts/tests.py`: minimal test that a created user gets a version-7 UUID pk and `get_user_model()` resolves to `accounts.User`

## 3. School models on UUID v7

- [x] 3.1 Create `src/school/models/base.py` with abstract `UUIDv7Model` (`id` UUID v7 pk via `uuid6.uuid7`)
- [x] 3.2 Make all 10 models inherit `UUIDv7Model`: `Student`, `Teacher`, `StudentGroup`, `Subject`, `Course`, `SchoolCycle`, `NonSchoolDay`, `AttendanceSession`, `AttendanceRecord`, `ClassSchedule` (no other field/Meta changes)
- [x] 3.3 Grep sweep for leftover integer-PK assumptions in `src/` (`<int:`, `session_id: int`, `id: int`, `int(value)` on ids) and note hits for groups 4–6

## 4. Panel and API id surfaces

- [x] 4.1 `src/teachers/urls.py`: convert all six `<int:pk>` routes to `<uuid:pk>`
- [x] 4.2 `src/api/api.py`: change `session_id: int` to `session_id: uuid.UUID`
- [x] 4.3 `src/api/schemas.py`: change `id: int` to `id: UUID` in `AttendanceRecordIn`, `AttendanceRecordOut`, `RecordError`
- [x] 4.4 `src/school/resources.py`: `NullableIdWidget.clean` returns `UUID(value)` (blank stays `None`); update return type hint; malformed ids surface as validation errors

## 5. Tests updated for UUID ids

- [x] 5.1 `src/api/tests.py`: replace `from django.contrib.auth.models import User` with `get_user_model()`; keep `create_user`/`force_login` usage
- [x] 5.2 `src/api/tests.py`: replace integer stand-ins — `{'id': 99999}` → fresh `uuid.uuid4()` string, `AttendanceSession(pk=99999)` → `AttendanceSession(pk=uuid.uuid4())`, reverse URLs keep working via object pk
- [x] 5.3 Run `uv run manage.py test` — all school/teachers/api tests pass (fix any stragglers found by the 3.3 sweep)

## 6. Database reset and migration regeneration

- [x] 6.1 Delete `db.sqlite3` and `src/school/migrations/000[1-8]*.py` (keep `__init__.py`); confirm `src/accounts/migrations/` and `src/teachers/migrations/` contain only `__init__.py`
- [x] 6.2 `uv run manage.py makemigrations accounts school` → review both `0001`s: every project table has UUID pk/FK/M2M columns, no AutoField remains on project models
- [x] 6.3 `uv run manage.py migrate` — clean run, no errors
- [x] 6.4 `uv run manage.py seed_dev_data` — superuser, teachers, students, groups, subjects, cycles, courses, schedules, attendance recreated with UUID ids

## 7. Verification

- [x] 7.1 `uv run manage.py check` passes
- [x] 7.2 Full suite `uv run manage.py test` green
- [x] 7.3 Smoke test: admin login as `admin`, open Student/SchoolCycle/AttendanceSession change pages (UUID in URL); teacher panel: dashboard → course → today session → save statuses via API-backed UI; `/api/docs` shows UUID `session_id` and record ids
- [x] 7.4 Verify round-trip import/export: export Students to CSV (UUID `id` column), re-import — updates in place; blank-id row creates new student
