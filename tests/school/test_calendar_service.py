"""Tests for school.services.calendar (session-date validation)."""

import re
from datetime import date
from datetime import time
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError

from school.models import ClassSchedule
from school.models import Course
from school.models import NonSchoolDay
from school.models import Subject
from school.services.calendar import validate_session_date

pytestmark = pytest.mark.django_db

MONDAY = date(2026, 1, 5)
TUESDAY = date(2026, 1, 6)
BEFORE_CYCLE = date(2025, 12, 31)
LAST_CYCLE_DAY = date(2026, 6, 30)
OUT_OF_CYCLE_MONDAY = date(2026, 7, 6)


def test_accepts_scheduled_date_inside_cycle(monday_course):
    validate_session_date(course=monday_course, value=MONDAY)


def test_accepts_first_day_of_cycle_when_scheduled(monday_course, school_cycle):
    assert school_cycle.start_date == MONDAY
    validate_session_date(course=monday_course, value=MONDAY)


def test_accepts_last_day_of_cycle_when_scheduled(course):
    ClassSchedule.objects.create(
        course=course,
        weekday=ClassSchedule.Weekday.TUESDAY,
        start_time=time(8, 0),
        end_time=time(9, 0),
    )

    validate_session_date(course=course, value=LAST_CYCLE_DAY)


def test_course_without_cycle_raises_related_object_does_not_exist(
    student_group,
    teacher,
):
    course = Course(
        student_group=student_group,
        teacher=teacher,
        subject=Subject.objects.create(name="Física"),
    )

    with pytest.raises(Course.school_cycle.RelatedObjectDoesNotExist):
        validate_session_date(course=course, value=MONDAY)


@pytest.mark.parametrize("value", [BEFORE_CYCLE, OUT_OF_CYCLE_MONDAY])
def test_rejects_date_outside_cycle(monday_course, value):
    with pytest.raises(ValidationError, match="fuera del ciclo"):
        validate_session_date(course=monday_course, value=value)


def test_rejects_non_school_day_with_formatted_date(monday_course, school_cycle):
    NonSchoolDay.objects.create(
        cycle=school_cycle,
        name="Día del maestro",
        day_type=NonSchoolDay.DayType.ASUETO,
        start_date=MONDAY,
    )

    with pytest.raises(
        ValidationError,
        match=re.escape("El 05/01/2026 es inhábil: Día del maestro."),
    ):
        validate_session_date(course=monday_course, value=MONDAY)


def test_rejects_non_school_day_range(monday_course, school_cycle):
    NonSchoolDay.objects.create(
        cycle=school_cycle,
        name="Semana de asueto",
        day_type=NonSchoolDay.DayType.VACACIONES,
        start_date=MONDAY,
        end_date=date(2026, 1, 9),
    )

    with pytest.raises(ValidationError, match="inhábil"):
        validate_session_date(course=monday_course, value=MONDAY)


def test_precomputed_non_school_day_skips_lookup_query(
    monday_course,
    django_assert_num_queries,
):
    non_school_day = NonSchoolDay(
        cycle_id=uuid4(),
        name="Día del maestro",
        day_type=NonSchoolDay.DayType.ASUETO,
        start_date=MONDAY,
    )

    with (
        django_assert_num_queries(0),
        pytest.raises(ValidationError, match="inhábil"),
    ):
        validate_session_date(
            course=monday_course,
            value=MONDAY,
            non_school_day=non_school_day,
        )


def test_rejects_course_without_schedule_slots(course):
    with pytest.raises(ValidationError, match="no tiene horario asignado"):
        validate_session_date(course=course, value=MONDAY)


def test_rejects_unscheduled_weekday(monday_course):
    with pytest.raises(ValidationError, match="no tiene clase los días martes"):
        validate_session_date(course=monday_course, value=TUESDAY)
