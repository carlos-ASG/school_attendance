"""Shared fixtures for the school test suite."""

from datetime import date
from datetime import time

import pytest

from school.models import AttendanceSession
from school.models import ClassSchedule
from school.models import Course
from school.models import SchoolCycle
from school.models import Student
from school.models import StudentGroup
from school.models import Subject
from school.models import Teacher

MONDAY = date(2026, 1, 5)


@pytest.fixture
def school_cycle(db):
    return SchoolCycle.objects.create(
        name="Ciclo 2026",
        cycle_type=SchoolCycle.CycleType.SEMESTRAL,
        start_date=date(2026, 1, 5),
        end_date=date(2026, 6, 30),
    )


@pytest.fixture
def teacher(db):
    return Teacher.objects.create(first_name="Ana", last_name="García")


@pytest.fixture
def student_group(db):
    return StudentGroup.objects.create(name="1A")


@pytest.fixture
def students(db, student_group):
    roster = [
        Student.objects.create(
            first_name="Beto",
            paternal_surname="López",
            maternal_surname="Ruiz",
        ),
        Student.objects.create(
            first_name="Carla",
            paternal_surname="Méndez",
            maternal_surname="Pérez",
        ),
        Student.objects.create(
            first_name="Diego",
            paternal_surname="Nava",
            maternal_surname="Ortiz",
        ),
    ]
    student_group.students.add(*roster)
    return roster


@pytest.fixture
def course(db, school_cycle, student_group, teacher):
    return Course.objects.create(
        school_cycle=school_cycle,
        student_group=student_group,
        teacher=teacher,
        subject=Subject.objects.create(name="Matemáticas"),
    )


@pytest.fixture
def monday_course(course):
    """Course whose only scheduled weekday is Monday."""
    ClassSchedule.objects.create(
        course=course,
        weekday=ClassSchedule.Weekday.MONDAY,
        start_time=time(8, 0),
        end_time=time(9, 0),
    )
    return course


@pytest.fixture
def session(db, monday_course, teacher):
    return AttendanceSession.objects.create(
        course=monday_course,
        date=MONDAY,
        created_by=teacher,
    )
