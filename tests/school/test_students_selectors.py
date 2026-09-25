"""Tests for school.selectors.students."""
from datetime import date
from uuid import uuid4

import pytest

from school.models import (
    Course,
    SchoolCycle,
    Student,
    StudentGroup,
    Subject,
    Teacher,
)
from school.selectors.students import course_students, get_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def school_cycle(db):
    return SchoolCycle.objects.create(
        name='Ciclo 2026',
        cycle_type=SchoolCycle.CycleType.SEMESTRAL,
        start_date=date(2026, 1, 5),
        end_date=date(2026, 6, 30),
    )


@pytest.fixture
def teacher(db):
    return Teacher.objects.create(first_name='Ana', last_name='García')


@pytest.fixture
def student_group(db):
    return StudentGroup.objects.create(name='1A')


@pytest.fixture
def course(db, school_cycle, student_group, teacher):
    return Course.objects.create(
        school_cycle=school_cycle,
        student_group=student_group,
        teacher=teacher,
        subject=Subject.objects.create(name='Matemáticas'),
    )


def make_student(first_name, paternal_surname, maternal_surname):
    return Student.objects.create(
        first_name=first_name,
        paternal_surname=paternal_surname,
        maternal_surname=maternal_surname,
    )


def test_get_student_returns_student_with_matching_id():
    student = make_student('Beto', 'López', 'Ruiz')

    assert get_student(student_id=student.id) == student


def test_get_student_unknown_id_returns_none():
    assert get_student(student_id=uuid4()) is None


def test_course_students_returns_only_group_members(course, student_group):
    in_group = [
        make_student('Beto', 'López', 'Ruiz'),
        make_student('Carla', 'Méndez', 'Pérez'),
    ]
    student_group.students.add(*in_group)
    other_group = StudentGroup.objects.create(name='1B')
    outsider = make_student('Diego', 'Nava', 'Ortiz')
    other_group.students.add(outsider)

    result = course_students(course=course)

    assert set(result) == set(in_group)


def test_course_students_empty_group_returns_nothing(course):
    assert not course_students(course=course).exists()