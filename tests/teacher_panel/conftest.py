"""Shared fixtures for the teacher_panel test suite."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model

from school.models import AttendanceRecord
from school.models import AttendanceSession
from school.models import Course
from school.models import SchoolCycle
from school.models import Student
from school.models import StudentGroup
from school.models import Subject
from school.models import Teacher

User = get_user_model()

MONDAY = date(2026, 1, 5)
TUESDAY = date(2026, 1, 6)
THURSDAY = date(2026, 1, 8)


@pytest.fixture
def teacher_user(db):
    user = User.objects.create_user(username="ana", password="test12345")
    Teacher.objects.create(first_name="Ana", last_name="García", user=user)
    return user


@pytest.fixture
def other_teacher_user(db):
    user = User.objects.create_user(username="raul", password="test12345")
    Teacher.objects.create(first_name="Raúl", last_name="Hdez", user=user)
    return user


@pytest.fixture
def school_cycle(db):
    return SchoolCycle.objects.create(
        name="Ciclo 2026",
        cycle_type=SchoolCycle.CycleType.SEMESTRAL,
        start_date=date(2026, 1, 5),
        end_date=date(2026, 6, 30),
    )


@pytest.fixture
def student_group(db):
    return StudentGroup.objects.create(name="1A")


@pytest.fixture
def students(db, student_group):
    beto = Student.objects.create(
        first_name="Beto",
        paternal_surname="López",
        maternal_surname="Ruiz",
    )
    carla = Student.objects.create(
        first_name="Carla",
        paternal_surname="Méndez",
        maternal_surname="Pérez",
    )
    student_group.students.add(beto, carla)
    return [beto, carla]


@pytest.fixture
def course(db, school_cycle, student_group, teacher_user):
    return Course.objects.create(
        school_cycle=school_cycle,
        student_group=student_group,
        teacher=Teacher.objects.get(user=teacher_user),
        subject=Subject.objects.create(name="Matemáticas"),
    )


@pytest.fixture
def teacher_client(client, teacher_user):
    client.force_login(teacher_user)
    return client


@pytest.fixture
def resumable_sessions(course, teacher_user, students):
    """One session on Monday, another on Thursday, with records for Beto."""
    monday = AttendanceSession.objects.create(
        course=course,
        date=MONDAY,
        created_by=Teacher.objects.get(user=teacher_user),
    )
    thursday = AttendanceSession.objects.create(
        course=course,
        date=THURSDAY,
        created_by=Teacher.objects.get(user=teacher_user),
    )
    beto = Student.objects.get(first_name="Beto")
    AttendanceRecord.objects.create(
        session=monday,
        student=beto,
        status=AttendanceRecord.Status.PRESENT,
    )
    AttendanceRecord.objects.create(
        session=thursday,
        student=beto,
        status=AttendanceRecord.Status.ABSENT,
    )
    return monday, thursday
