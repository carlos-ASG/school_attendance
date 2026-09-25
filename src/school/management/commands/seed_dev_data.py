"""Preload development data into the database (idempotent)."""

from datetime import date
from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from school.models import AttendanceRecord
from school.models import AttendanceSession
from school.models import ClassSchedule
from school.models import Course
from school.models import NonSchoolDay
from school.models import SchoolCycle
from school.models import Student
from school.models import StudentGroup
from school.models import Subject
from school.models import Teacher

DEV_PASSWORD = "dev12345"

MONTHS_ES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def month_name(value: date) -> str:
    return MONTHS_ES[value.month - 1].capitalize()


def cycle_name(start: date, end: date) -> str:
    return f"{month_name(start)} – {month_name(end)} {end.year}"


def demo_cycle() -> dict[str, Any]:
    """SEMESTRAL cycle spanning today (±60 days, 121 days long).

    Dates are computed from today so the demo data is always current; only
    this function changes if the demo window ever needs adjusting.
    """
    today = timezone.now().date()
    start = today - timedelta(days=60)
    end = today + timedelta(days=60)
    revolution = date(start.year, 11, 20)
    if not start <= revolution <= end:
        revolution = start + timedelta(days=30)
    christmas_start = max(date(start.year, 12, 21), start)
    christmas_end = min(date(start.year, 12, 31), end)
    if christmas_start > christmas_end:
        christmas_start = end - timedelta(days=10)
        christmas_end = end
    return {
        "name": cycle_name(start, end),
        "cycle_type": SchoolCycle.CycleType.SEMESTRAL,
        "start_date": start,
        "end_date": end,
        "non_school_days": [
            {
                "name": "Día de la Revolución",
                "day_type": NonSchoolDay.DayType.ASUETO,
                "start_date": revolution,
                "end_date": None,
            },
            {
                "name": "Vacaciones de navidad",
                "day_type": NonSchoolDay.DayType.VACACIONES,
                "start_date": christmas_start,
                "end_date": christmas_end,
            },
        ],
    }


def past_cycle() -> dict[str, Any]:
    """SEMESTRAL cycle entirely before the demo cycle (131 days, no overlap)."""
    demo_start = timezone.now().date() - timedelta(days=60)
    end = demo_start - timedelta(days=30)
    start = end - timedelta(days=130)
    easter = start + timedelta(days=60)
    labor = start + timedelta(days=90)
    return {
        "name": cycle_name(start, end),
        "cycle_type": SchoolCycle.CycleType.SEMESTRAL,
        "start_date": start,
        "end_date": end,
        "non_school_days": [
            {
                "name": "Semana Santa",
                "day_type": NonSchoolDay.DayType.VACACIONES,
                "start_date": easter,
                "end_date": easter + timedelta(days=4),
            },
            {
                "name": "Día del Trabajo",
                "day_type": NonSchoolDay.DayType.ASUETO,
                "start_date": labor,
                "end_date": None,
            },
        ],
    }


# Where attendance sessions are seeded from:
#   ('today', n)      -> date.today() + n days (relative to any run date)
#   ('cycle_end', n)  -> cycle end_date + n days (fixed inside the cycle)
CYCLE_CONFIGS = [
    {
        "cycle": demo_cycle(),
        "attendance_anchor": ("today", -7),
        "mixed_status": False,
    },
    {
        "cycle": past_cycle(),
        "attendance_anchor": ("cycle_end", -14),
        "mixed_status": True,
    },
]

TEACHERS = [
    {"username": "teacher1", "first_name": "Ana", "last_name": "García"},
    {"username": "teacher2", "first_name": "Luis", "last_name": "Martínez"},
    {"username": "teacher3", "first_name": "María", "last_name": "López"},
]

STUDENTS = [
    ("Juan", "Pérez", "Gómez"),
    ("Sofía", "Ramírez", "Flores"),
    ("Diego", "Hernández", "Ruiz"),
    ("Valeria", "Torres", "Vega"),
    ("Mateo", "Sánchez", "Morales"),
    ("Camila", "Vargas", "Castro"),
    ("Sebastián", "Mendoza", "Ríos"),
    ("Lucía", "Ávila", "Peña"),
]

SUBJECTS = [
    {"name": "Matemáticas", "code": "MAT"},
    {"name": "Lengua y Literatura", "code": "LEN"},
    {"name": "Ciencias Naturales", "code": "CIE"},
]

GROUPS = ["1° A", "1° B"]

COURSES = [
    (
        "1° A",
        "Matemáticas",
        "teacher1",
        "Aula 101",
        [(0, "08:00", "09:00"), (2, "08:00", "09:00")],
    ),
    (
        "1° A",
        "Lengua y Literatura",
        "teacher2",
        "Aula 101",
        [(1, "08:00", "09:00"), (4, "08:00", "09:00")],
    ),
    ("1° A", "Ciencias Naturales", "teacher3", "Aula 102", [(0, "09:00", "10:00")]),
    (
        "1° B",
        "Matemáticas",
        "teacher2",
        "Aula 201",
        [(0, "10:00", "11:00"), (3, "10:00", "11:00")],
    ),
    ("1° B", "Lengua y Literatura", "teacher3", "Aula 201", [(2, "10:00", "11:00")]),
    ("1° B", "Ciencias Naturales", "teacher1", "Aula 202", [(1, "09:00", "10:00")]),
]

STUDENTS_PER_GROUP = 5


class Command(BaseCommand):
    help = (
        "Preload development data (cycles, users, teachers, students, "
        "groups, subjects, courses, schedules, attendance)"
    )

    def handle(self, *args: Any, **options: Any) -> None:
        self.create_superuser()
        teachers = self.create_teachers()
        groups = self.create_student_groups()
        subjects = self.create_subjects()
        for config in CYCLE_CONFIGS:
            cycle = self.create_school_cycle(config)
            courses = self.create_courses(cycle, groups, subjects, teachers)
            self.create_attendance(courses, cycle, config)
        self.stdout.write(self.style.SUCCESS("Dev data preloaded successfully."))

    def create_school_cycle(self, config: dict[str, Any]) -> SchoolCycle:
        data = config["cycle"]
        cycle, created = SchoolCycle.objects.get_or_create(
            name=data["name"],
            defaults={
                "cycle_type": data["cycle_type"],
                "start_date": data["start_date"],
                "end_date": data["end_date"],
            },
        )
        for day in data["non_school_days"]:
            NonSchoolDay.objects.get_or_create(
                cycle=cycle,
                name=day["name"],
                defaults={
                    "day_type": day["day_type"],
                    "start_date": day["start_date"],
                    "end_date": day["end_date"],
                },
            )
        action = "Created" if created else "Skipped"
        cycle.refresh_from_db()  # SQLite keeps raw strings on new objects
        self.stdout.write(f'{action} school cycle "{cycle.name}".')
        return cycle

    def create_superuser(self) -> None:
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "Dev",
                "is_staff": True,
                "is_superuser": True,
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
                username=data["username"],
                defaults={
                    "email": f"{data['username']}@example.com",
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                },
            )
            if user_created:
                user.set_password(DEV_PASSWORD)
                user.save()
            teacher, teacher_created = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                },
            )
            teachers[data["username"]] = teacher
            action = "Created" if user_created and teacher_created else "Skipped"
            self.stdout.write(f'{action} teacher "{data["username"]}".')
        return teachers

    def create_student_groups(self) -> dict[str, StudentGroup]:
        groups = {}
        for index, name in enumerate(GROUPS):
            group, created = StudentGroup.objects.get_or_create(name=name)
            group_students = []
            for first, paternal, maternal in STUDENTS[
                index * STUDENTS_PER_GROUP : (index + 1) * STUDENTS_PER_GROUP
            ]:
                student, _ = Student.objects.get_or_create(
                    first_name=first,
                    paternal_surname=paternal,
                    maternal_surname=maternal,
                )
                group_students.append(student)
            group.students.set(group_students)
            groups[name] = group
            action = "Created" if created else "Updated"
            self.stdout.write(
                f'{action} student group "{name}" ({len(group_students)} students).'
            )
        return groups

    def create_subjects(self) -> dict[str, Subject]:
        subjects = {}
        for data in SUBJECTS:
            subject, _ = Subject.objects.get_or_create(
                name=data["name"],
                defaults={"code": data["code"]},
            )
            subjects[data["name"]] = subject
        self.stdout.write(f"Ensured {len(SUBJECTS)} subjects.")
        return subjects

    def create_courses(
        self,
        cycle: SchoolCycle,
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
                school_cycle=cycle,
                defaults={"classroom": classroom},
            )
            for weekday, start, end in slots:
                ClassSchedule.objects.get_or_create(
                    course=course,
                    weekday=weekday,
                    start_time=start,
                    end_time=end,
                )
            courses.append(course)
            action = "Created" if created else "Skipped"
            self.stdout.write(
                f"{action} course {course} ({len(slots)} schedule slots)."
            )
        return courses

    def attendance_base_date(self, cycle: SchoolCycle, config: dict[str, Any]) -> date:
        anchor, offset = config["attendance_anchor"]
        if anchor == "cycle_end":
            return cycle.end_date + timedelta(days=offset)
        return timezone.now().date() + timedelta(days=offset)

    def create_attendance(
        self, courses: list[Course], cycle: SchoolCycle, config: dict[str, Any]
    ) -> None:
        base = self.attendance_base_date(cycle, config)
        statuses = list(AttendanceRecord.Status)
        sessions_created = 0
        records_created = 0
        for index, course in enumerate(courses):
            session, created = AttendanceSession.objects.get_or_create(
                course=course,
                date=base + timedelta(days=index),
                defaults={"created_by": course.teacher},
            )
            if not created:
                continue
            sessions_created += 1
            for student_index, student in enumerate(
                course.student_group.students.all()
            ):
                if config["mixed_status"]:
                    status = statuses[(student_index + index) % len(statuses)]
                else:
                    status = AttendanceRecord.Status.PRESENT
                AttendanceRecord.objects.get_or_create(
                    session=session,
                    student=student,
                    defaults={"status": status},
                )
                records_created += 1
        self.stdout.write(
            f"Created {sessions_created} attendance sessions "
            f'({records_created} records) for "{cycle.name}".',
        )
