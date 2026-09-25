"""Tests for school.selectors.sessions."""

from datetime import date

import pytest

from school.models import AttendanceSession
from school.models import Course
from school.models import SchoolCycle
from school.models import StudentGroup
from school.models import Subject
from school.models import Teacher
from school.selectors.sessions import course_history_sessions
from school.selectors.sessions import get_today_session
from school.selectors.sessions import teacher_sessions

pytestmark = pytest.mark.django_db

MONDAY = date(2026, 1, 5)
TUESDAY = date(2026, 1, 6)
WEDNESDAY = date(2026, 1, 7)


def create_course(teacher, subject_name):
    cycle = SchoolCycle.objects.create(
        name=f"Ciclo {subject_name}",
        cycle_type=SchoolCycle.CycleType.SEMESTRAL,
        start_date=MONDAY,
        end_date=date(2026, 6, 30),
    )
    return Course.objects.create(
        school_cycle=cycle,
        student_group=StudentGroup.objects.create(name=f"1A {subject_name}"),
        teacher=teacher,
        subject=Subject.objects.create(name=subject_name),
    )


def create_session(course, teacher, value):
    return AttendanceSession.objects.create(
        course=course,
        date=value,
        created_by=teacher,
    )


def test_teacher_sessions_returns_only_that_teachers_sessions(teacher):
    teacher_b = Teacher.objects.create(first_name="Luis", last_name="Martínez")
    own = create_session(
        create_course(teacher, "Matemáticas"),
        teacher,
        MONDAY,
    )
    create_session(create_course(teacher_b, "Historia"), teacher_b, MONDAY)

    assert set(teacher_sessions(teacher=teacher)) == {own}


def test_teacher_sessions_is_optimized_single_query(
    teacher,
    django_assert_num_queries,
):
    course = create_course(teacher, "Matemáticas")
    create_session(course, teacher, MONDAY)

    with django_assert_num_queries(1):
        for session in teacher_sessions(teacher=teacher):
            _ = (
                session.course.subject,
                session.course.student_group,
                session.course.school_cycle,
                session.created_by,
            )


def test_course_history_sessions_excludes_value_and_keeps_others(
    monday_course,
    teacher,
):
    monday = create_session(monday_course, teacher, MONDAY)
    wednesday = create_session(monday_course, teacher, WEDNESDAY)
    create_session(monday_course, teacher, TUESDAY)

    result = course_history_sessions(course=monday_course, value=TUESDAY)

    assert set(result) == {monday, wednesday}
    assert list(result) == [wednesday, monday]


def test_get_today_session_returns_session_on_date(monday_course, teacher):
    session = create_session(monday_course, teacher, MONDAY)

    assert get_today_session(course=monday_course, value=MONDAY) == session


def test_get_today_session_returns_none_without_session(monday_course, teacher):
    create_session(monday_course, teacher, MONDAY)

    assert get_today_session(course=monday_course, value=TUESDAY) is None


def test_get_today_session_scopes_to_course(teacher):
    other_teacher = Teacher.objects.create(
        first_name="Luis",
        last_name="Martínez",
    )
    other_course = create_course(other_teacher, "Historia")
    create_session(other_course, other_teacher, MONDAY)

    assert get_today_session(course=other_course, value=MONDAY) is not None
    course = create_course(teacher, "Matemáticas")
    assert get_today_session(course=course, value=MONDAY) is None
