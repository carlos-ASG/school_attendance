"""Tests for school.selectors.teachers."""
import pytest

from school.models import Teacher
from school.selectors.teachers import get_teacher

pytestmark = pytest.mark.django_db


def make_teacher(user, first_name='Ana', last_name='García'):
    return Teacher.objects.create(
        user=user, first_name=first_name, last_name=last_name
    )


def test_get_teacher_returns_teacher_linked_to_user(django_user_model):
    user = django_user_model.objects.create_user(username='ana')
    teacher = make_teacher(user)

    assert get_teacher(user=user) == teacher


def test_get_teacher_user_without_teacher_profile_returns_none(django_user_model):
    user = django_user_model.objects.create_user(username='luis')

    assert get_teacher(user=user) is None


def test_get_teacher_returns_correct_teacher_among_many(django_user_model):
    user_a = django_user_model.objects.create_user(username='ana')
    user_b = django_user_model.objects.create_user(username='luis')
    make_teacher(user_a)
    teacher_b = make_teacher(user_b, first_name='Luis', last_name='Martínez')

    assert get_teacher(user=user_b) == teacher_b


def test_get_teacher_unlinked_teacher_does_not_match(django_user_model):
    user = django_user_model.objects.create_user(username='ana')
    make_teacher(user=None)

    assert get_teacher(user=user) is None
