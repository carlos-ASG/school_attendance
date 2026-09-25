"""Tests for school.services.sessions (write services)."""

from datetime import UTC
from datetime import date
from datetime import datetime

import pytest
from django.core.exceptions import ValidationError

from school import services
from school.models import AttendanceRecord
from school.models import AttendanceSession
from school.models import NonSchoolDay

pytestmark = pytest.mark.django_db

MONDAY = date(2026, 1, 5)  # inside the cycle below, and scheduled
TUESDAY = date(2026, 1, 6)  # inside the cycle, not scheduled
OUT_OF_CYCLE_MONDAY = date(2026, 7, 6)  # after the cycle ends


def test_create_attendance_records_one_present_record_per_student(
    session,
    students,
):
    created = services.create_attendance_records(session)

    assert created == 3
    assert session.records.count() == 3
    assert set(session.records.values_list("student_id", flat=True)) == {
        s.id for s in students
    }
    assert all(
        record.status == AttendanceRecord.Status.PRESENT
        for record in session.records.all()
    )


def test_create_attendance_records_skips_existing_and_is_idempotent(
    session,
    students,
):
    AttendanceRecord.objects.create(session=session, student=students[0])

    created = services.create_attendance_records(session)

    assert created == 2
    assert session.records.count() == 3
    # Second call is a no-op (idempotent).
    assert services.create_attendance_records(session) == 0
    assert session.records.count() == 3


def test_create_attendance_records_empty_group_creates_nothing(course, teacher):
    session = AttendanceSession.objects.create(
        course=course,
        date=MONDAY,
        created_by=teacher,
    )

    assert services.create_attendance_records(session) == 0
    assert session.records.count() == 0


def test_session_create_persists_session_and_one_record_per_student(
    monday_course,
    teacher,
    students,
):
    session = services.session_create(
        course=monday_course,
        value=MONDAY,
        created_by=teacher,
    )

    assert AttendanceSession.objects.filter(
        pk=session.pk,
        course=monday_course,
        date=MONDAY,
        created_by=teacher,
    ).exists()
    assert session.records.count() == len(students)


def test_get_or_create_creates_session_for_scheduled_date(
    monday_course,
    teacher,
    students,
):
    session, created = services.session_get_or_create_today(
        course=monday_course,
        created_by=teacher,
        value=MONDAY,
    )

    assert created
    assert session.date == MONDAY
    assert session.records.count() == len(students)


def test_get_or_create_value_defaults_to_today(monkeypatch, monday_course, teacher):
    monkeypatch.setattr(
        "django.utils.timezone.now",
        lambda: datetime(2026, 1, 5, 12, 0, tzinfo=UTC),
    )

    session, created = services.session_get_or_create_today(
        course=monday_course,
        created_by=teacher,
    )

    assert created
    assert session.date == MONDAY


def test_get_or_create_returns_existing_without_revalidating(course, teacher):
    # `course` has no schedule slots, so MONDAY is calendar-invalid:
    # if the service re-validated existing sessions this would raise.
    existing = AttendanceSession.objects.create(
        course=course,
        date=MONDAY,
        created_by=teacher,
    )

    session, created = services.session_get_or_create_today(
        course=course,
        created_by=teacher,
        value=MONDAY,
    )

    assert not created
    assert session == existing


def test_get_or_create_rejects_date_outside_cycle(monday_course, teacher):
    with pytest.raises(ValidationError, match="fuera del ciclo"):
        services.session_get_or_create_today(
            course=monday_course,
            created_by=teacher,
            value=OUT_OF_CYCLE_MONDAY,
        )
    assert not AttendanceSession.objects.exists()


def test_get_or_create_rejects_non_school_day(monday_course, teacher, school_cycle):
    NonSchoolDay.objects.create(
        cycle=school_cycle,
        name="Día del maestro",
        day_type=NonSchoolDay.DayType.ASUETO,
        start_date=MONDAY,
    )

    with pytest.raises(ValidationError, match="inhábil"):
        services.session_get_or_create_today(
            course=monday_course,
            created_by=teacher,
            value=MONDAY,
        )
    assert not AttendanceSession.objects.exists()


def test_get_or_create_rejects_weekday_without_schedule_slots(
    monday_course,
    teacher,
):
    with pytest.raises(ValidationError, match="martes"):
        services.session_get_or_create_today(
            course=monday_course,
            created_by=teacher,
            value=TUESDAY,
        )
    assert not AttendanceSession.objects.exists()


def test_get_or_create_rejects_course_without_schedule(course, teacher):
    with pytest.raises(ValidationError, match="horario"):
        services.session_get_or_create_today(
            course=course,
            created_by=teacher,
            value=MONDAY,
        )
    assert not AttendanceSession.objects.exists()


def test_session_delete_removes_session_and_its_records(
    monday_course,
    teacher,
    students,
):
    session, _ = services.session_get_or_create_today(
        course=monday_course,
        created_by=teacher,
        value=MONDAY,
    )

    services.session_delete(session=session)

    assert not AttendanceSession.objects.filter(pk=session.pk).exists()
    assert not AttendanceRecord.objects.exists()
