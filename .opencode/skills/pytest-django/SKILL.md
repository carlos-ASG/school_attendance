---
name: pytest-django
description: Use when writing, running, or debugging Django tests in this repo — pytest-django markers (@pytest.mark.django_db), fixtures (client, db, settings, mailoutbox, django_assert_num_queries), test database behavior (config.test_settings, in-memory SQLite), pytest invocations, or test_*.py files. Co-load django-style when testing services/selectors.
license: MIT
---

# pytest-django in this repo

Tests run with pytest, never `manage.py test`. Tests live in the root
**`tests/` folder, one subfolder per app**: `tests/<app>/test_<topic>.py`.
App packages are importable directly (`uv run` installs the project
editable) — no `__init__.py` or sys.path tricks needed in `tests/`.
Working reference: `tests/school/test_example.py` — copy its shape.

## Commands

```
uv run pytest                        # whole suite
uv run pytest tests/school/test_example.py -v   # one file
uv run pytest -k dashboard           # by name substring
uv run pytest -x                     # stop at first failure
uv run pytest --no-migrations        # faster DB setup
```

## Project config (already wired — do not re-create)

- `pyproject.toml` → `[tool.pytest.ini_options]`:
  `DJANGO_SETTINGS_MODULE = "config.test_settings"`,
  `python_files = ["test_*.py", "tests.py"]`, `testpaths = ["tests"]`,
  `addopts = "--import-mode=importlib"` (same-named files in different
  subfolders are safe; no `__init__.py` in `tests/`).
- `src/config/test_settings.py` = `config.settings` + **in-memory SQLite**.
  The suite never needs the PostgreSQL server from `.env` (`DATABASE_URL`).
- `pytest` + `pytest-django` are dev dependencies (`[dependency-groups] dev`);
  production images built with `uv sync --no-dev` exclude them.

## The four core patterns

```python
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from school.models import Teacher

User = get_user_model()


@pytest.mark.django_db                      # 1. grant database access
def test_create_teacher():
    teacher = Teacher.objects.create(first_name='Ana', last_name='García')
    assert str(teacher) == 'Ana García'     # plain asserts, no self.assert*


@pytest.fixture                             # 2. reusable test data
def teacher_user(db):                       # `db` gives the FIXTURE db access
    user = User.objects.create_user(username='ana', password='test12345')
    Teacher.objects.create(first_name='Ana', last_name='García', user=user)
    return user


@pytest.mark.django_db
def test_dashboard_redirects_anonymous_to_login(client):   # 3. test browser
    response = client.get(reverse('teacher_panel:dashboard'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_dashboard_renders_for_teacher(client, teacher_user):
    client.force_login(teacher_user)        # 4. authenticate the client
    assert client.get(reverse('teacher_panel:dashboard')).status_code == 200
```

Mark database access at exactly ONE level: module (`pytestmark =
pytest.mark.django_db`), class (`@pytest.mark.django_db` above the class), or
single function. Stacking levels is redundant.

## Plain functions first — classes are optional

pytest does not need unittest-style classes; the four patterns above are the
idiom. Reach for a class only to (a) group related tests in a large file or
(b) attach an `autouse` fixture to just that group:

```python
@pytest.mark.django_db
class TestUserPermissions:
    @pytest.fixture(autouse=True)
    def setup_role(self):
        self.role = 'admin'   # runs before each test in this class only

    def test_admin_access(self):
        assert self.role == 'admin'
```

Class rules: name starts with `Test`, no `__init__` method, and never inherit
from `unittest.TestCase` (that disables pytest's fixture injection).

## Choosing a fixture or marker

| Need | Use |
| --- | --- |
| Query/insert models | `@pytest.mark.django_db` on the test |
| Custom fixture that touches the DB | request the `db` fixture in it |
| Request pages as a user | `client` + `client.force_login(user)` |
| Hit admin as superuser | `admin_client` (creates user `admin`) |
| Create users generically | `django_user_model` fixture |
| Build requests for a view directly | `rf` (no middleware!) |
| Override a setting for one test | `settings` fixture (auto-reverts) |
| Assert on sent email | `mailoutbox` |
| Catch N+1 / query regressions | `django_assert_num_queries(n)` |
| Django's TestCase asserts | `from pytest_django.asserts import assertContains, ...` |

Full fixture docs: `references/fixtures.md`.
Database access rules, `--reuse-db`, transactional tests, DB-config
overrides: `references/database.md`.

## Gotchas

- **DB access is blocked by default.** A test touching the ORM without the
  marker (or a `db`-style fixture) fails on purpose — add the marker.
- **One marker level is enough.** Module `pytestmark` OR class decorator OR
  per-function `@pytest.mark.django_db` — never more than one.
- **The marker on a test does NOT grant DB access to its fixtures' setup
  code** (pytest fixture ordering). Request `db` inside the fixture.
- Test DB is throwaway in-memory SQLite — tests can never touch
  `db.sqlite3` or the Postgres in `.env`.
- `--reuse-db` is pointless here: in-memory SQLite is recreated instantly
  each run (and per xdist worker, via `pytest -n auto`).
- Tests run with `DEBUG=False` by default (`django_debug_mode`).
- Co-load the `django-style` skill when the code under test is a service or
  selector.
