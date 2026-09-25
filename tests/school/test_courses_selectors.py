"""Tests for school.selectors.courses."""

from datetime import date
from datetime import timedelta

import pytest
from django.utils import timezone

from school.models import ClassSchedule
from school.models import Course
from school.models import SchoolCycle
from school.models import StudentGroup
from school.models import Subject
from school.models import Teacher
from school.selectors.courses import teacher_courses
from school.selectors.courses import teacher_current_courses
from school.selectors.courses import teacher_previous_cycle_courses

pytestmark = pytest.mark.django_db


def make_cycle(name, start_date, end_date):
    return SchoolCycle.objects.create(
        name=name,
        cycle_type=SchoolCycle.CycleType.SEMESTRAL,
        start_date=start_date,
        end_date=end_date,
    )


def make_course(teacher, subject_name, cycle, group_name):
    return Course.objects.create(
        school_cycle=cycle,
        student_group=StudentGroup.objects.create(name=group_name),
        teacher=teacher,
        subject=Subject.objects.create(name=subject_name),
    )


# teacher_courses


def test_teacher_courses_returns_only_that_teachers_courses(
    teacher,
    school_cycle,
    course,
):
    other_teacher = Teacher.objects.create(first_name="Luis", last_name="Martínez")
    make_course(other_teacher, "Historia", school_cycle, "1B")

    assert set(teacher_courses(teacher=teacher)) == {course}


def test_teacher_courses_is_optimized(teacher, course, django_assert_num_queries):
    ClassSchedule.objects.create(
        course=course,
        weekday=ClassSchedule.Weekday.MONDAY,
        start_time=timezone.localtime().time(),
        end_time=timezone.localtime().time(),
    )

    with django_assert_num_queries(3):
        for fetched in teacher_courses(teacher=teacher):
            _ = (
                fetched.subject,
                fetched.teacher,
                fetched.student_group,
                fetched.school_cycle,
            )
            assert list(fetched.student_group.students.all()) == []
            assert list(fetched.schedule_slots.all()) != []


# teacher_current_courses


def test_teacher_current_courses_without_cycle_returns_empty(teacher, course):
    queryset = teacher_current_courses(teacher=teacher, school_cycle=None)

    assert not queryset.exists()


def test_teacher_current_courses_scopes_to_cycle_and_teacher(
    teacher,
    school_cycle,
    course,
):
    other_teacher = Teacher.objects.create(first_name="Luis", last_name="Martínez")
    previous_cycle = make_cycle("Ciclo anterior", date(2025, 8, 4), date(2025, 12, 19))
    previous_course = make_course(teacher, "Historia", previous_cycle, "1B")
    make_course(other_teacher, "Cívica", school_cycle, "1C")

    assert set(
        teacher_current_courses(teacher=teacher, school_cycle=school_cycle)
    ) == {course}
    assert set(
        teacher_current_courses(teacher=teacher, school_cycle=previous_cycle)
    ) == {previous_course}


def test_teacher_current_courses_annotates_student_count(
    teacher,
    school_cycle,
    course,
    students,
):
    empty_course = make_course(teacher, "Historia", school_cycle, "1B")

    result = teacher_current_courses(teacher=teacher, school_cycle=school_cycle)
    counts = {
        fetched.subject.name: fetched.student_count for fetched in result
    }

    assert counts == {"Matemáticas": 3, "Historia": 0}


def test_teacher_current_courses_is_optimized(
    teacher,
    school_cycle,
    course,
    students,
    django_assert_num_queries,
):
    with django_assert_num_queries(2):
        for fetched in teacher_current_courses(
            teacher=teacher,
            school_cycle=school_cycle,
        ):
            _ = (
                fetched.subject,
                fetched.teacher,
                fetched.student_group,
                fetched.school_cycle,
                fetched.student_count,
            )
            assert list(fetched.schedule_slots.all()) == []


# teacher_previous_cycle_courses


def test_teacher_previous_cycle_courses_returns_cycles_ended_before_anchor(
    teacher,
    school_cycle,
    course,
):
    previous_cycle = make_cycle("Ciclo anterior", date(2025, 8, 4), date(2025, 12, 1))
    previous_course = make_course(teacher, "Historia", previous_cycle, "1B")
    overlapping_cycle = make_cycle(
        "Ciclo traslapado",
        date(2025, 10, 6),
        date(2026, 3, 2),
    )
    make_course(teacher, "Cívica", overlapping_cycle, "1C")

    result = teacher_previous_cycle_courses(teacher=teacher, school_cycle=school_cycle)

    assert set(result) == {previous_course}


def test_teacher_previous_cycle_courses_without_cycle_anchors_to_today(teacher):
    today = timezone.now().date()
    finished_cycle = make_cycle(
        "Ciclo finalizado",
        today - timedelta(days=300),
        today - timedelta(days=50),
    )
    finished_course = make_course(teacher, "Historia", finished_cycle, "1A")
    ongoing_cycle = make_cycle(
        "Ciclo en curso",
        today - timedelta(days=30),
        today + timedelta(days=150),
    )
    make_course(teacher, "Matemáticas", ongoing_cycle, "1B")
    future_cycle = make_cycle(
        "Ciclo futuro",
        today + timedelta(days=200),
        today + timedelta(days=400),
    )
    make_course(teacher, "Cívica", future_cycle, "1C")

    result = teacher_previous_cycle_courses(teacher=teacher, school_cycle=None)

    assert set(result) == {finished_course}


def test_teacher_previous_cycle_courses_orders_by_cycle_then_subject(
    teacher,
    school_cycle,
):
    older_cycle = make_cycle("Ciclo viejo", date(2025, 8, 4), date(2025, 11, 21))
    newer_cycle = make_cycle("Ciclo nuevo", date(2025, 11, 24), date(2025, 12, 19))
    older_history = make_course(teacher, "Historia", older_cycle, "1A")
    older_maths = make_course(teacher, "Matemáticas", older_cycle, "1B")
    newer_civics = make_course(teacher, "Cívica", newer_cycle, "1C")
    make_course(teacher, "Arte", school_cycle, "1D")

    result = list(
        teacher_previous_cycle_courses(teacher=teacher, school_cycle=school_cycle)
    )

    assert result == [older_history, older_maths, newer_civics]
