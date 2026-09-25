"""Tests for school.selectors.attendance."""

from datetime import date

import pytest

from school.models import AttendanceRecord
from school.models import AttendanceSession
from school.models import Course
from school.models import Subject
from school.selectors.attendance import get_course_attendance_summary
from school.selectors.attendance import get_student_attendance_summary

pytestmark = pytest.mark.django_db

MONDAY = date(2026, 1, 5)
TUESDAY = date(2026, 1, 6)
WEDNESDAY = date(2026, 1, 7)
THURSDAY = date(2026, 1, 8)


def create_session(course, teacher, value):
    return AttendanceSession.objects.create(
        course=course,
        date=value,
        created_by=teacher,
    )


def create_record(session, student, status):
    return AttendanceRecord.objects.create(
        session=session,
        student=student,
        status=status,
    )


# get_course_attendance_summary


def test_course_summary_without_sessions_returns_zeroed_summary(course, students):
    summary = get_course_attendance_summary(course=course)

    assert set(summary) == {student.pk for student in students}
    for student in students:
        row = summary[student.pk]
        assert row["student"] == student
        assert row["attended"] == 0
        assert row["total"] == 0
        assert row["percentage"] == "0"


def test_course_summary_counts_attended_statuses(course, teacher, students):
    beto, carla, diego = students
    monday = create_session(course, teacher, MONDAY)
    tuesday = create_session(course, teacher, TUESDAY)
    wednesday = create_session(course, teacher, WEDNESDAY)
    create_record(monday, beto, AttendanceRecord.Status.PRESENT)
    create_record(tuesday, beto, AttendanceRecord.Status.LATE)
    create_record(wednesday, beto, AttendanceRecord.Status.ABSENT)
    create_record(monday, carla, AttendanceRecord.Status.EXCUSED)

    summary = get_course_attendance_summary(course=course)

    assert summary[beto.pk]["attended"] == 2
    assert summary[beto.pk]["total"] == 3
    assert summary[beto.pk]["percentage"] == "66.7"
    assert summary[carla.pk]["attended"] == 1
    assert summary[carla.pk]["percentage"] == "33.3"
    assert summary[diego.pk]["attended"] == 0
    assert summary[diego.pk]["percentage"] == "0.0"


def test_course_summary_scopes_records_to_course(
    teacher,
    school_cycle,
    student_group,
    students,
    course,
):
    beto = students[0]
    create_session(course, teacher, MONDAY)
    other_course = Course.objects.create(
        school_cycle=school_cycle,
        student_group=student_group,
        teacher=teacher,
        subject=Subject.objects.create(name="Historia"),
    )
    other_session = create_session(other_course, teacher, MONDAY)
    create_record(other_session, beto, AttendanceRecord.Status.PRESENT)

    summary = get_course_attendance_summary(course=course)

    assert summary[beto.pk]["total"] == 1
    assert summary[beto.pk]["attended"] == 0
    assert summary[beto.pk]["percentage"] == "0.0"


def test_course_summary_uses_bounded_queries(
    course,
    teacher,
    students,
    django_assert_num_queries,
):
    beto, carla, diego = students
    session = create_session(course, teacher, MONDAY)
    for student in (beto, carla, diego):
        create_record(session, student, AttendanceRecord.Status.PRESENT)

    with django_assert_num_queries(3):
        summary = get_course_attendance_summary(course=course)
        _ = summary[beto.pk]["percentage"]


# get_student_attendance_summary


def test_student_summary_without_sessions_returns_zeroed(course, students):
    beto = students[0]

    result = get_student_attendance_summary(course=course, student=beto)

    assert result == {"attended": 0, "total": 0, "percentage": "0"}


def test_student_summary_counts_only_that_students_records(
    teacher,
    school_cycle,
    student_group,
    students,
    course,
):
    beto, carla, diego = students
    monday = create_session(course, teacher, MONDAY)
    tuesday = create_session(course, teacher, TUESDAY)
    wednesday = create_session(course, teacher, WEDNESDAY)
    thursday = create_session(course, teacher, THURSDAY)
    create_record(monday, beto, AttendanceRecord.Status.PRESENT)
    create_record(tuesday, beto, AttendanceRecord.Status.LATE)
    create_record(wednesday, beto, AttendanceRecord.Status.EXCUSED)
    create_record(thursday, beto, AttendanceRecord.Status.ABSENT)
    create_record(monday, carla, AttendanceRecord.Status.PRESENT)
    create_record(tuesday, carla, AttendanceRecord.Status.ABSENT)
    other_course = Course.objects.create(
        school_cycle=school_cycle,
        student_group=student_group,
        teacher=teacher,
        subject=Subject.objects.create(name="Historia"),
    )
    other_session = create_session(other_course, teacher, THURSDAY)
    create_record(other_session, beto, AttendanceRecord.Status.PRESENT)

    beto_result = get_student_attendance_summary(course=course, student=beto)
    carla_result = get_student_attendance_summary(course=course, student=carla)
    diego_result = get_student_attendance_summary(course=course, student=diego)

    assert beto_result == {"attended": 3, "total": 4, "percentage": "75.0"}
    assert carla_result == {"attended": 1, "total": 4, "percentage": "25.0"}
    assert diego_result == {"attended": 0, "total": 4, "percentage": "0.0"}
