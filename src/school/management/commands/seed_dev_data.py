"""Preload development data into the database (idempotent)."""
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from school.models import (
    AttendanceRecord,
    AttendanceSession,
    ClassSchedule,
    Course,
    Student,
    StudentGroup,
    Subject,
    Teacher,
)

DEV_PASSWORD = 'dev12345'

TEACHERS = [
    {'username': 'teacher1', 'first_name': 'Ana', 'last_name': 'García'},
    {'username': 'teacher2', 'first_name': 'Luis', 'last_name': 'Martínez'},
    {'username': 'teacher3', 'first_name': 'María', 'last_name': 'López'},
]

STUDENTS = [
    ('Juan', 'Pérez', 'Gómez'),
    ('Sofía', 'Ramírez', 'Flores'),
    ('Diego', 'Hernández', 'Ruiz'),
    ('Valeria', 'Torres', 'Vega'),
    ('Mateo', 'Sánchez', 'Morales'),
    ('Camila', 'Vargas', 'Castro'),
    ('Sebastián', 'Mendoza', 'Ríos'),
    ('Lucía', 'Ávila', 'Peña'),
]

SUBJECTS = [
    {'name': 'Matemáticas', 'code': 'MAT'},
    {'name': 'Lengua y Literatura', 'code': 'LEN'},
    {'name': 'Ciencias Naturales', 'code': 'CIE'},
]

GROUPS = ['1° A', '1° B']

COURSES = [
    ('1° A', 'Matemáticas', 'teacher1', 'Aula 101', [(0, '08:00', '09:00'), (2, '08:00', '09:00')]),
    ('1° A', 'Lengua y Literatura', 'teacher2', 'Aula 101', [(1, '08:00', '09:00'), (4, '08:00', '09:00')]),
    ('1° A', 'Ciencias Naturales', 'teacher3', 'Aula 102', [(0, '09:00', '10:00')]),
    ('1° B', 'Matemáticas', 'teacher2', 'Aula 201', [(0, '10:00', '11:00'), (3, '10:00', '11:00')]),
    ('1° B', 'Lengua y Literatura', 'teacher3', 'Aula 201', [(2, '10:00', '11:00')]),
    ('1° B', 'Ciencias Naturales', 'teacher1', 'Aula 202', [(1, '09:00', '10:00')]),
]

STUDENTS_PER_GROUP = 5


class Command(BaseCommand):
    help = 'Preload development data (users, teachers, students, groups, subjects, courses, schedules)'

    def handle(self, *args: Any, **options: Any) -> None:
        self.create_superuser()
        teachers = self.create_teachers()
        groups = self.create_student_groups()
        subjects = self.create_subjects()
        courses = self.create_courses(groups, subjects, teachers)
        self.create_attendance(courses)
        self.stdout.write(self.style.SUCCESS('Dev data preloaded successfully.'))

    def create_superuser(self) -> None:
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'Dev',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            user.set_password(DEV_PASSWORD)
            user.save()
            self.stdout.write('Created superuser "admin" (password: dev12345).')
        else:
            self.stdout.write('Superuser "admin" already exists, skipped.')

    def create_teachers(self) -> dict[str, Teacher]:
        User = get_user_model()
        teachers = {}
        for data in TEACHERS:
            user, user_created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': f"{data['username']}@example.com",
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                },
            )
            if user_created:
                user.set_password(DEV_PASSWORD)
                user.save()
            teacher, teacher_created = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                },
            )
            teachers[data['username']] = teacher
            action = 'Created' if user_created and teacher_created else 'Skipped'
            self.stdout.write(f'{action} teacher "{data["username"]}".')
        return teachers

    def create_student_groups(self) -> dict[str, StudentGroup]:
        groups = {}
        for index, name in enumerate(GROUPS):
            group, created = StudentGroup.objects.get_or_create(name=name)
            group_students = []
            for first, paternal, maternal in STUDENTS[
                index * STUDENTS_PER_GROUP:(index + 1) * STUDENTS_PER_GROUP
            ]:
                student, _ = Student.objects.get_or_create(
                    first_name=first,
                    paternal_surname=paternal,
                    maternal_surname=maternal,
                )
                group_students.append(student)
            group.students.set(group_students)
            groups[name] = group
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action} student group "{name}" ({len(group_students)} students).')
        return groups

    def create_subjects(self) -> dict[str, Subject]:
        subjects = {}
        for data in SUBJECTS:
            subject, _ = Subject.objects.get_or_create(
                name=data['name'],
                defaults={'code': data['code']},
            )
            subjects[data['name']] = subject
        self.stdout.write(f'Ensured {len(SUBJECTS)} subjects.')
        return subjects

    def create_courses(
        self,
        groups: dict[str, StudentGroup],
        subjects: dict[str, Subject],
        teachers: dict[str, Teacher],
    ) -> list[Course]:
        courses = []
        for group_name, subject_name, teacher_username, classroom, slots in COURSES:
            course, created = Course.objects.get_or_create(
                student_group=groups[group_name],
                teacher=teachers[teacher_username],
                subject=subjects[subject_name],
                defaults={'classroom': classroom},
            )
            for weekday, start, end in slots:
                ClassSchedule.objects.get_or_create(
                    course=course,
                    weekday=weekday,
                    start_time=start,
                    end_time=end,
                )
            courses.append(course)
            action = 'Created' if created else 'Skipped'
            self.stdout.write(f'{action} course {course} ({len(slots)} schedule slots).')
        return courses

    def create_attendance(self, courses: list[Course]) -> None:
        from datetime import date, timedelta

        sessions_created = 0
        records_created = 0
        base = date.today() - timedelta(days=7)
        for index, course in enumerate(courses):
            session, created = AttendanceSession.objects.get_or_create(
                course=course,
                date=base + timedelta(days=index),
                defaults={'created_by': course.teacher},
            )
            if not created:
                continue
            sessions_created += 1
            for student in course.student_group.students.all():
                record, _ = AttendanceRecord.objects.get_or_create(
                    session=session,
                    student=student,
                    defaults={'status': AttendanceRecord.Status.PRESENT},
                )
                records_created += 1
        self.stdout.write(
            f'Created {sessions_created} attendance sessions ({records_created} records).'
        )
