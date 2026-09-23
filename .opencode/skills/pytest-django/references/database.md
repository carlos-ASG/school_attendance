# pytest-django: database access & configuration

## Blocked by default (by design)

Any ORM access without explicit opt-in fails. Opt in per test, per class, or
per module:

```python
@pytest.mark.django_db
def test_one(): ...

@pytest.mark.django_db
class TestUsers: ...          # class-level

pytestmark = pytest.mark.django_db   # module-level
```

Each test runs inside a transaction that is rolled back afterwards — same
isolation as Django's `TestCase`, so tests never see each other's rows.

## Marker arguments

| Arg | When |
| --- | --- |
| `transaction=True` | Code under test manages its own transactions / spawns threads (TransactionTestCase semantics). Slower. |
| `databases=['default', 'other']` (or `'__all__'`) | Multi-DB setups (not used here today). |
| `reset_sequences=True` | Needs `transaction=True`; resets auto-increment pks (SQLite support varies). |
| `serialized_rollback=True` | Restore data-migration data in transactional tests. ~3x slower. |

## Fixtures vs marker inside custom fixtures

The `django_db` marker on a **test** does not reliably grant DB access to the
setup code of fixtures that test requests. Inside any fixture that uses the
ORM, request `db` (rollback isolation) or `transactional_db` (real commits):

```python
@pytest.fixture
def teacher_user(db):            # <- this line is what grants access
    user = get_user_model().objects.create_user('ana', password='x1234567')
    Teacher.objects.create(first_name='Ana', last_name='García', user=user)
    return user
```

## CLI options

```
uv run pytest --no-migrations        # build schema from models, skip migrations (fast)
uv run pytest -n auto                # pytest-xdist parallel (NOT installed; add if suite grows)
```

- `--reuse-db` / `--create-db`: cache the test DB across runs; schema changes
  require `--create-db`. **Moot in this repo** — the DB is in-memory SQLite,
  recreated instantly every run.
- With xdist, each worker gets its own DB (`*_gw0`, `*_gw1`, ...); tests never
  share rows across workers.

## This repo's DB configuration (important)

Tests always run on **in-memory SQLite** because
`pyproject.toml` → `[tool.pytest.ini_options]` sets
`DJANGO_SETTINGS_MODULE = "config.test_settings"`, and
`src/config/test_settings.py` overrides `DATABASES` **before Django boots**.

Practical consequences:

1. The Postgres server from `.env` (`DATABASE_URL`) is never contacted; tests
   can't corrupt `db.sqlite3` or dev data.
2. **Do not** try to switch the test DB from a `conftest.py` fixture
   (`django_db_modify_db_settings` override). It runs *after* the connection
   wrapper snapshot and silently keeps pointing at the `.env` Postgres —
   learned the hard way. Change DB config in `test_settings.py` only.
3. To add test-only settings generally, put them in `config/test_settings.py`
   (imported from `config.settings` via `from .settings import *`).

## Session-wide seed data recipe

Run the existing idempotent dev seeder once per session (optional pattern for
integration-heavy suites):

```python
# conftest.py (root)
import pytest
from django.core.management import call_command


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('seed_dev_data')   # get_or_create based — safe to rerun
```

Notes: `django_db_blocker` lifts the "db blocked" guard during setup; data is
loaded once and visible to all `django_db` tests (it is NOT rolled back
between tests — per-test unique rows still belong in per-test fixtures).

## Overridable fixtures (custom DB setups)

All overridable in `conftest.py` at the same scope: `django_db_setup`
(top-level creation; override to point at a template/external DB),
`django_db_use_migrations`, `django_db_keepdb`, `django_db_createdb`,
`django_db_modify_db_settings` (+ its `_tox_suffix` / `_xdist_suffix`
chain — override it to `pass` if you want all xdist workers sharing one DB).
See https://pytest-django.readthedocs.io/en/stable/database.html for worked
examples. In this repo prefer `test_settings.py` (see above).

## DEBUG and template strictness

- Tests run with `DEBUG=False` regardless of `.env` (production-like output).
- Opt-in template strictness: `[tool.pytest.ini_options]` →
  `FAIL_INVALID_TEMPLATE_VARS = true` fails tests whose templates reference
  invalid variables; escape hatch per test: `@pytest.mark.ignore_template_errors`.
