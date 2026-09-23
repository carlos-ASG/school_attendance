"""Minimal pytest-django examples — a reference for writing new tests.

Run all tests:        uv run pytest
Run just this file:   uv run pytest src/school/test_example.py -v

What you see below:
- tests are plain functions named test_*
- assertions are plain `assert`, no self.assertEqual needed
- @pytest.mark.django_db lets a test touch the database (each test gets
  a clean, throwaway database automatically)
- fixtures (@pytest.fixture) build reusable test data; a test uses one by
  listing its name as a parameter
- `client` is a built-in pytest-django fixture: Django's test browser
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from school.models import Teacher

User = get_user_model()


# --- 1. Model test: create rows, assert on them ------------------------


@pytest.mark.django_db
def test_create_teacher():
    user = User.objects.create_user(username='luis', password='test12345')
    teacher = Teacher.objects.create(
        first_name='Luis', last_name='Martínez', user=user
    )
    assert teacher.pk is not None
    assert str(teacher) == 'Luis Martínez'
    assert Teacher.objects.count() == 1


# --- 2. Fixture: reusable test data shared by several tests ------------
# `db` (built-in) gives fixture setup database access, so tests that ask
# for `teacher_user` don't need the django_db mark themselves.


@pytest.fixture
def teacher_user(db):
    user = User.objects.create_user(username='ana', password='test12345')
    Teacher.objects.create(first_name='Ana', last_name='García', user=user)
    return user


# --- 3. View tests: `client` is the test browser ------------------------


@pytest.mark.django_db
def test_dashboard_redirects_anonymous_to_login(client):
    response = client.get(reverse('teacher_panel:dashboard'))
    assert response.status_code == 302
    assert reverse('account_login') in response.url


@pytest.mark.django_db
def test_dashboard_renders_for_teacher(client, teacher_user):
    client.force_login(teacher_user)
    response = client.get(reverse('teacher_panel:dashboard'))
    assert response.status_code == 200
