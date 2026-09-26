"""View tests for the course attendance summary page (day filters via HTMX)."""

from datetime import date
from urllib.parse import urlencode

import pytest
from django.urls import reverse

from school.models import Student
from tests.teacher_panel.conftest import TUESDAY

pytestmark = pytest.mark.django_db


def summary_url(course, **params):
    url = reverse("teacher_panel:course_attendance_summary", args=[course.pk])
    if params:
        url = f"{url}?{urlencode(params)}"
    return url


def assert_summary_row(response, student, text):
    content = response.content.decode()
    student_url = reverse(
        "teacher_panel:course_student_detail",
        args=[response.context["course"].pk, student.pk],
    )
    assert f'href="{student_url}"' in content
    assert text in content


def test_summary_without_filters_matches_course_detail_totals(
    teacher_client,
    course,
    resumable_sessions,
):
    beto = Student.objects.get(first_name="Beto")

    response = teacher_client.get(summary_url(course))

    assert response.status_code == 200
    assert_summary_row(response, beto, "1/2 (50.0%)")


def test_summary_form_target_survives_the_swap(teacher_client, course):
    """Regression: outerHTML swap removed #attendance-summary from the DOM,
    so the second filter attempt had no target. The wrapper div must stay in
    place (outside the partial) and the swap must be innerHTML."""

    response = teacher_client.get(summary_url(course))

    content = response.content.decode()
    assert 'id="attendance-summary"' in content
    assert 'hx-target="#attendance-summary-content"' in content
    assert 'hx-indicator="#attendance-summary"' in content
    assert 'hx-swap="innerHTML"' in content
    assert 'htmx-indicator' in content  # in-flight block spinner + "Cargando…"
    assert 'animate-spin' in content
    assert "Cargando…" in content
    assert 'hx-disabled-elt=".filter-actions"' in content
    assert content.count("filter-actions") == 4  # 2 selectors + both buttons


def test_summary_double_filter_responds_both_times(
    teacher_client,
    course,
    resumable_sessions,
):
    beto = Student.objects.get(first_name="Beto")
    htmx = {"HX-Request": "true"}

    first = teacher_client.get(
        summary_url(course, date_from="2026-01-05", date_to="2026-01-05"),
        headers=htmx,
    )
    second = teacher_client.get(
        summary_url(course, date_from="2026-01-08", date_to="2026-01-08"),
        headers=htmx,
    )

    assert first.status_code == second.status_code == 200
    assert_summary_row(second, beto, "0/1 (0.0%)")


def test_summary_filters_by_date_range_via_htmx_fragment(
    teacher_client,
    course,
    resumable_sessions,
):
    beto = Student.objects.get(first_name="Beto")

    response = teacher_client.get(
        summary_url(course, date_from="2026-01-05", date_to="2026-01-05"),
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "extends" not in content
    assert "Resumen de asistencia — Panel del Profesor" not in content
    assert 'id="attendance-summary"' not in content  # fragment replaces it
    assert_summary_row(response, beto, "1/1 (100.0%)")


def test_summary_full_page_with_query_scopes_the_range(
    teacher_client,
    course,
    resumable_sessions,
):
    beto = Student.objects.get(first_name="Beto")

    response = teacher_client.get(
        summary_url(course, date_from="2026-01-05", date_to="2026-01-05"),
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="attendance-summary"' in content  # full page keeps the shell
    assert_summary_row(response, beto, "1/1 (100.0%)")


def test_summary_open_upper_bound(teacher_client, course, resumable_sessions):
    beto = Student.objects.get(first_name="Beto")

    response = teacher_client.get(summary_url(course, date_from=TUESDAY.isoformat()))

    assert_summary_row(response, beto, "0/1 (0.0%)")


def test_summary_open_lower_bound(teacher_client, course, resumable_sessions):
    beto = Student.objects.get(first_name="Beto")

    response = teacher_client.get(summary_url(course, date_to=TUESDAY.isoformat()))

    assert_summary_row(response, beto, "1/1 (100.0%)")


def test_summary_range_without_sessions_shows_empty_state(
    teacher_client,
    course,
    resumable_sessions,
):
    response = teacher_client.get(
        summary_url(course, date_from=TUESDAY.isoformat(), date_to=TUESDAY.isoformat()),
    )

    content = response.content.decode()
    assert "No hay sesiones en el rango seleccionado." in content


def test_summary_invalid_range_shows_error_without_table(
    teacher_client,
    course,
    resumable_sessions,
):
    beto = Student.objects.get(first_name="Beto")

    response = teacher_client.get(
        summary_url(course, date_from="2026-01-06", date_to="2026-01-05"),
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "La fecha inicial no puede ser posterior a la fecha final." in content
    assert not summary_row_rendered(response, beto)


def summary_row_rendered(response, student):
    return student.first_name in response.content.decode()


def test_summary_of_another_teachers_course_is_404(
    teacher_client,
    course,
    school_cycle,
    student_group,
    other_teacher_user,
):
    from school.models import Course
    from school.models import Subject
    from school.models import Teacher

    other_course = Course.objects.create(
        school_cycle=school_cycle,
        student_group=student_group,
        teacher=Teacher.objects.get(user=other_teacher_user),
        subject=Subject.objects.create(name="Historia"),
    )

    response = teacher_client.get(summary_url(other_course))

    assert response.status_code == 404


def test_summary_requires_authentication(client, course):
    response = client.get(summary_url(course))

    assert response.status_code == 302
    assert "login" in response.url


def test_summary_non_teacher_user_is_denied(client, teacher_user, course):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    plain_user = User.objects.create_user(username="juan", password="test12345")
    client.force_login(plain_user)

    response = client.get(summary_url(course))

    assert response.status_code == 403


def test_summary_entry_button_on_course_detail(teacher_client, course):
    response = teacher_client.get(
        reverse("teacher_panel:course_detail", args=[course.pk]),
    )

    assert summary_url(course) in response.content.decode()
