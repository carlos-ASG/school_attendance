# pytest-django fixtures cheat-sheet

Fixtures are requested by adding their name as a test (or fixture) parameter.
Examples use this repo's models/URLs where possible.

## `client` — Django test browser (`django.test.Client`)

Requests full URLs through the URL conf (middleware included). Pairs with
`reverse()` and `force_login()`:

```python
@pytest.mark.django_db
def test_dashboard_renders_for_teacher(client, teacher_user):
    client.force_login(teacher_user)
    response = client.get(reverse('teacher_panel:dashboard'))
    assert response.status_code == 200
    assert 'Ana García' in response.content.decode()
```

- Anonymous user hitting a `TeacherRequiredMixin` view → 302 to
  `reverse('account_login')` + `?next=...`.
- Authenticated user **without** a linked `Teacher` → 403 (PermissionDenied).
- POST forms: `client.post(url, {'field': 'value'})`; JSON APIs:
  `client.post(url, data, content_type='application/json')`.

## `admin_client` / `admin_user`

`admin_user`: superuser (username `admin`, password `password`), created on
demand. `admin_client`: `client` already force-logged-in as it. Both imply
database access — no marker needed:

```python
def test_admin_dashboard(admin_client):
    assert admin_client.get('/admin/').status_code == 200
```

## `django_user_model` — AUTH_USER_MODEL as a class

This project's user is `accounts.User` (UUID pk). Use the fixture instead of
importing so tests stay decoupled:

```python
@pytest.mark.django_db
def test_password(django_user_model):
    user = django_user_model.objects.create_user('pepe', password='test12345')
    assert user.check_password('test12345')
```

## `rf` — RequestFactory

Calls a view function directly — **middleware does NOT run**, so set
`request.user` yourself:

```python
from teacher_panel.views.dashboard import DashboardView

@pytest.mark.django_db
def test_dashboard_queryset(rf, teacher_user):
    request = rf.get('/teacher/')
    request.user = teacher_user
    response = DashboardView.as_view()(request)
    assert response.status_code == 200
```

`async_rf` is the async counterpart (needs `pytest-asyncio`, not installed).

## `db` / `transactional_db` — database access for fixtures

- `db`: session DB wrapped in a per-test transaction that rolls back (same
  isolation as `@pytest.mark.django_db`).
- `transactional_db`: real commits + table truncation between tests; slower;
  required for code that manages its own `transaction.atomic()`/threads.
- Equivalent marker args: `@pytest.mark.django_db(transaction=True)`.

**Rule:** a custom fixture that touches the ORM must request `db` (or
`transactional_db`) — the marker on the *test* does not cover fixture setup:

```python
@pytest.fixture
def students(db):
    from school.models.factories import Student  # if factories exist
    return [Student.objects.create(first_name=f'A{i}') for i in range(3)]
```

## `settings` — override Django settings per test

Automatically reverted after the test:

```python
def test_login_required_redirect(settings):
    settings.LOGIN_URL = '/custom-login/'
    ...
```

Type annotation: `settings: pytest_django.Settings`. (Django's
`override_settings` decorator also works alongside pytest.)

## `mailoutbox` — sent emails

Clean outbox per test:

```python
def test_welcome_email(mailoutbox):
    send_welcome(...)          # anything using django.core.mail
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ['ana@example.com']
```

Project note: most app email goes through the `MAILERS` console backend
(dev-only setting). `mailoutbox` intercepts `django.core.mail` locmem
sends; if the code path writes to the console backend instead, capture
stdout with pytest's `capsys` fixture and assert on that.

## `django_assert_num_queries` / `django_assert_max_num_queries`

Catch N+1 and missing `select_related`:

```python
@pytest.mark.django_db
def test_teacher_courses_query_count(django_assert_num_queries, teacher_user):
    from school.selectors.courses import teacher_current_courses
    teacher = teacher_user.teacher
    with django_assert_num_queries(3):
        list(teacher_current_courses(teacher=teacher, school_cycle=None))
```

Run with `-v` to print the offending SQL on failure. Prefer the `_max_`
variant when the exact count is brittle.

## `django_capture_on_commit_callbacks`

Run/inspect `transaction.on_commit()` callbacks without committing:

```python
def test_side_effect_scheduled(client, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        client.post('/api/things/', {...}, content_type='application/json')
    assert len(callbacks) == 1
```

Avoid in `transaction=True` tests — results are unreliable there.

## `live_server`

Background-thread Django server (`live_server.url`); implies
`transactional_db`. Only needed for browser/e2e tests (none today).

## `pytest_django.asserts` — Django's TestCase asserts as functions

```python
from pytest_django.asserts import (
    assertContains, assertRedirects, assertTemplateUsed, assertNumQueries,
)

def test_page(client):
    response = client.get('/')
    assertContains(response, 'Bienvenido', status_code=200)
    assertTemplateUsed(response, 'teacher_panel/dashboard.html')
```
