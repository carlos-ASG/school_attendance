from datetime import date, timedelta

from typing import Any

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .admin import AttendanceRecordInline
from .calendar import (
    get_active_cycle,
    get_non_school_day,
    validate_session_date,
)
from .models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    NonSchoolDay,
    SchoolCycle,
    Student,
    StudentGroup,
    Subject,
    Teacher,
)


def make_cycle(
    name: str = 'Ciclo Test',
    cycle_type: str = SchoolCycle.CycleType.SEMESTRAL,
    start: date | None = None,
    end: date | None = None,
) -> SchoolCycle:
    """Create a SEMESTRAL cycle spanning today (±60 days, 121 days long)."""
    today = timezone.now().date()
    return SchoolCycle.objects.create(
        name=name,
        cycle_type=cycle_type,
        start_date=start or today - timedelta(days=60),
        end_date=end or today + timedelta(days=60),
    )


def make_course_data(
    group_name: str,
) -> tuple[StudentGroup, Student, Student, Teacher, Course]:
    group = StudentGroup.objects.create(name=group_name)
    insider = Student.objects.create(
        first_name='Ana', paternal_surname='Pérez', maternal_surname='López'
    )
    outsider = Student.objects.create(
        first_name='Luis', paternal_surname='García', maternal_surname='Ruiz'
    )
    group.students.add(insider)
    teacher = Teacher.objects.create(first_name='María', last_name='Díaz')
    subject = Subject.objects.create(name=f'Materia {group_name}')
    course = Course.objects.create(
        student_group=group, teacher=teacher, subject=subject, school_cycle=make_cycle()
    )
    return group, insider, outsider, teacher, course


class AttendanceRecordCleanTests(TestCase):
    def setUp(self) -> None:
        _, self.insider, self.outsider, self.teacher, self.course = make_course_data(
            'Grupo Clean'
        )
        self.session = AttendanceSession.objects.create(
            course=self.course, date='2026-09-10', created_by=self.teacher
        )

    def test_insider_student_is_valid(self):
        record = AttendanceRecord(session=self.session, student=self.insider)
        record.full_clean()
        record.save()
        self.assertEqual(record.student, self.insider)

    def test_outsider_student_raises_validation_error(self):
        record = AttendanceRecord(session=self.session, student=self.outsider)
        with self.assertRaises(ValidationError):
            record.full_clean()


class AttendanceSessionCleanTests(TestCase):
    def setUp(self) -> None:
        _, _, _, self.teacher, self.course = make_course_data('Grupo Sesiones')

    def test_future_date_raises_validation_error(self):
        session = AttendanceSession(
            course=self.course,
            date=timezone.now().date() + timedelta(days=1),
            created_by=self.teacher,
        )
        with self.assertRaises(ValidationError):
            session.full_clean()

    def test_today_is_allowed(self):
        session = AttendanceSession(
            course=self.course, date=timezone.now().date(), created_by=self.teacher
        )
        session.full_clean()
        session.save()
        self.assertTrue(AttendanceSession.objects.filter(pk=session.pk).exists())

    def test_past_date_is_allowed(self):
        session = AttendanceSession(
            course=self.course,
            date=timezone.now().date() - timedelta(days=1),
            created_by=self.teacher,
        )
        session.full_clean()
        session.save()
        self.assertTrue(AttendanceSession.objects.filter(pk=session.pk).exists())

    def test_out_of_cycle_date_rejected(self) -> None:
        session = AttendanceSession(
            course=self.course,
            date=self.course.school_cycle.start_date - timedelta(days=1),
            created_by=self.teacher,
        )
        with self.assertRaises(ValidationError) as ctx:
            session.full_clean()
        self.assertIn(str(self.course.school_cycle), str(ctx.exception.messages))

    def test_non_school_day_rejected(self) -> None:
        date = timezone.now().date() - timedelta(days=2)
        NonSchoolDay.objects.create(
            cycle=self.course.school_cycle,
            name='Día de prueba',
            day_type=NonSchoolDay.DayType.ASUETO,
            start_date=date,
        )
        session = AttendanceSession(
            course=self.course, date=date, created_by=self.teacher
        )
        with self.assertRaises(ValidationError) as ctx:
            session.full_clean()
        self.assertIn('Día de prueba', str(ctx.exception.messages))
        self.assertFalse(
            AttendanceSession.objects.filter(course=self.course, date=date).exists()
        )

    def test_existing_session_survives_later_calendar_change(self) -> None:
        session = AttendanceSession(
            course=self.course,
            date=timezone.now().date() - timedelta(days=2),
            created_by=self.teacher,
        )
        session.full_clean()
        session.save()
        NonSchoolDay.objects.create(
            cycle=self.course.school_cycle,
            name='Día posterior',
            day_type=NonSchoolDay.DayType.ASUETO,
            start_date=session.date,
        )
        session.full_clean()  # editing an existing session stays allowed
        session.save()
        self.assertTrue(AttendanceSession.objects.filter(pk=session.pk).exists())


class AttendanceRecordInlineTests(TestCase):
    def setUp(self) -> None:
        _, self.insider, self.outsider, self.teacher, self.course = make_course_data(
            'Grupo Inline'
        )
        self.session = AttendanceSession.objects.create(
            course=self.course, date='2026-09-11', created_by=self.teacher
        )

    def test_student_choices_limited_to_group(self):
        request = RequestFactory().get(
            f'/admin/school/attendancesession/{self.session.pk}/change/'
        )
        request.resolver_match = type(
            'ResolverMatch', (), {'kwargs': {'object_id': str(self.session.pk)}}
        )()
        inline = AttendanceRecordInline(AttendanceSession, admin.site)
        field = inline.formfield_for_foreignkey(
            AttendanceRecord._meta.get_field('student'), request
        )
        self.assertIn(self.insider, field.queryset)
        self.assertNotIn(self.outsider, field.queryset)

    def test_student_choices_empty_without_session(self):
        request = RequestFactory().get('/admin/school/attendancesession/add/')
        request.resolver_match = type(
            'ResolverMatch', (), {'kwargs': {'object_id': None}}
        )()
        inline = AttendanceRecordInline(AttendanceSession, admin.site)
        field = inline.formfield_for_foreignkey(
            AttendanceRecord._meta.get_field('student'), request
        )
        self.assertEqual(field.queryset.count(), 0)


class SchoolCycleValidationTests(TestCase):
    def test_start_not_before_end_rejected(self) -> None:
        today = timezone.now().date()
        cycle = SchoolCycle(
            name='Ciclo invertido',
            cycle_type=SchoolCycle.CycleType.SEMESTRAL,
            start_date=today,
            end_date=today,
        )
        with self.assertRaises(ValidationError):
            cycle.full_clean()

    def test_short_annual_cycle_rejected(self) -> None:
        today = timezone.now().date()
        cycle = SchoolCycle(
            name='Ciclo anual corto',
            cycle_type=SchoolCycle.CycleType.ANNUAL,
            start_date=today,
            end_date=today + timedelta(days=80),
        )
        with self.assertRaises(ValidationError):
            cycle.full_clean()

    def test_real_length_semester_accepted(self) -> None:
        cycle = SchoolCycle(
            name='Ciclo semestral real',
            cycle_type=SchoolCycle.CycleType.SEMESTRAL,
            start_date=date(2026, 8, 18),
            end_date=date(2026, 12, 12),
        )
        cycle.full_clean()

    def test_real_length_quatrimestre_accepted(self) -> None:
        cycle = SchoolCycle(
            name='Ciclo cuatrimestral real',
            cycle_type=SchoolCycle.CycleType.QUATRIMESTRAL,
            start_date=date(2026, 9, 7),
            end_date=date(2026, 12, 19),
        )
        cycle.full_clean()

    def test_overlapping_cycle_rejected_and_names_conflict(self) -> None:
        existing = make_cycle('Ciclo Existente')
        today = timezone.now().date()
        overlapping = SchoolCycle(
            name='Ciclo Traslapado',
            cycle_type=SchoolCycle.CycleType.SEMESTRAL,
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=90),
        )
        with self.assertRaises(ValidationError) as ctx:
            overlapping.full_clean()
        self.assertIn('Ciclo Existente', str(ctx.exception.messages))

    def test_adjacent_cycle_allowed(self) -> None:
        existing = make_cycle(
            'Ciclo A', start=timezone.now().date() - timedelta(days=60)
        )
        adjacent = SchoolCycle(
            name='Ciclo B',
            cycle_type=SchoolCycle.CycleType.SEMESTRAL,
            start_date=existing.end_date + timedelta(days=1),
            end_date=existing.end_date + timedelta(days=130),
        )
        adjacent.full_clean()

    def test_gapped_cycle_allowed(self) -> None:
        existing = make_cycle(
            'Ciclo A', start=timezone.now().date() - timedelta(days=200)
        )
        gapped = SchoolCycle(
            name='Ciclo B',
            cycle_type=SchoolCycle.CycleType.SEMESTRAL,
            start_date=existing.end_date + timedelta(days=30),
            end_date=existing.end_date + timedelta(days=160),
        )
        gapped.full_clean()


class NonSchoolDayCleanTests(TestCase):
    def setUp(self) -> None:
        self.cycle = make_cycle()

    def make_day(self, **overrides: Any) -> NonSchoolDay:
        data = {
            'cycle': self.cycle,
            'name': 'Día inhábil',
            'day_type': NonSchoolDay.DayType.ASUETO,
            'start_date': timezone.now().date(),
        }
        data.update(overrides)
        return NonSchoolDay(**data)

    def test_single_day_valid(self) -> None:
        day = self.make_day()
        day.full_clean()
        day.save()
        self.assertIsNone(day.end_date)

    def test_vacation_range_valid(self) -> None:
        day = self.make_day(
            name='Vacaciones',
            day_type=NonSchoolDay.DayType.VACACIONES,
            end_date=timezone.now().date() + timedelta(days=5),
        )
        day.full_clean()
        day.save()

    def test_end_before_start_rejected(self) -> None:
        day = self.make_day(end_date=timezone.now().date() - timedelta(days=1))
        with self.assertRaises(ValidationError):
            day.full_clean()

    def test_range_outside_cycle_rejected(self) -> None:
        day = self.make_day(
            end_date=self.cycle.end_date + timedelta(days=1)
        )
        with self.assertRaises(ValidationError) as ctx:
            day.full_clean()
        self.assertIn(str(self.cycle), str(ctx.exception.messages))

    def test_overlapping_entries_allowed(self) -> None:
        first = self.make_day(name='A', end_date=timezone.now().date() + timedelta(days=3))
        first.full_clean()
        first.save()
        second = self.make_day(
            name='B', start_date=timezone.now().date() + timedelta(days=1)
        )
        second.full_clean()
        second.save()
        self.assertEqual(self.cycle.non_school_days.count(), 2)


class CourseCycleUniquenessTests(TestCase):
    def setUp(self) -> None:
        group = StudentGroup.objects.create(name='Grupo Ciclo')
        teacher = Teacher.objects.create(first_name='Ana', last_name='García')
        subject = Subject.objects.create(name='Materia Ciclo')
        self.group, self.teacher, self.subject = group, teacher, subject
        self.cycle_a = make_cycle('Ciclo A')
        self.cycle_b = make_cycle('Ciclo B')

    def test_same_trio_in_two_cycles_allowed(self) -> None:
        first = Course.objects.create(
            student_group=self.group,
            teacher=self.teacher,
            subject=self.subject,
            school_cycle=self.cycle_a,
        )
        second = Course.objects.create(
            student_group=self.group,
            teacher=self.teacher,
            subject=self.subject,
            school_cycle=self.cycle_b,
        )
        self.assertNotEqual(first.pk, second.pk)

    def test_duplicate_within_cycle_rejected(self) -> None:
        Course.objects.create(
            student_group=self.group,
            teacher=self.teacher,
            subject=self.subject,
            school_cycle=self.cycle_a,
        )
        with self.assertRaises(IntegrityError):
            Course.objects.create(
                student_group=self.group,
                teacher=self.teacher,
                subject=self.subject,
                school_cycle=self.cycle_a,
            )


class CalendarHelperTests(TestCase):
    def setUp(self) -> None:
        _, _, _, _, self.course = make_course_data('Grupo Calendar')

    def test_get_active_cycle_returns_cycle_containing_date(self) -> None:
        self.assertEqual(get_active_cycle(timezone.now().date()), self.course.school_cycle)
        self.assertIsNone(
            get_active_cycle(self.course.school_cycle.end_date + timedelta(days=10))
        )

    def test_get_non_school_day_matches_single_and_range(self) -> None:
        single = NonSchoolDay.objects.create(
            cycle=self.course.school_cycle,
            name='Asueto único',
            day_type=NonSchoolDay.DayType.ASUETO,
            start_date=timezone.now().date() - timedelta(days=3),
        )
        matched = get_non_school_day(
            self.course.school_cycle, timezone.now().date() - timedelta(days=3)
        )
        self.assertEqual(matched, single)
        self.assertIsNone(
            get_non_school_day(self.course.school_cycle, timezone.now().date())
        )

    def test_validate_session_date_allows_in_cycle_normal_date(self) -> None:
        validate_session_date(self.course, timezone.now().date() - timedelta(days=1))

    def test_validate_session_date_rejects_non_school_day(self) -> None:
        date = timezone.now().date() - timedelta(days=2)
        NonSchoolDay.objects.create(
            cycle=self.course.school_cycle,
            name='Inhábil nombrado',
            day_type=NonSchoolDay.DayType.ASUETO,
            start_date=date,
        )
        with self.assertRaises(ValidationError) as ctx:
            validate_session_date(self.course, date)
        self.assertIn('Inhábil nombrado', str(ctx.exception.messages))

    def test_validate_session_date_rejects_out_of_cycle(self) -> None:
        date = self.course.school_cycle.end_date + timedelta(days=5)
        with self.assertRaises(ValidationError) as ctx:
            validate_session_date(self.course, date)
        self.assertIn(str(self.course.school_cycle), str(ctx.exception.messages))


class SchoolCycleAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = get_user_model().objects.create_superuser('root', 'root@example.com', 'pass')

    def setUp(self) -> None:
        self.client.force_login(self.admin_user)
        self.cycle = make_cycle('Ciclo Admin')

    def test_cycle_add_page_renders_inline(self) -> None:
        response = self.client.get(
            reverse('admin:school_schoolcycle_add')
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Días inhábiles')

    def test_cycle_change_page_allows_inline_non_school_day(self) -> None:
        response = self.client.post(
            reverse('admin:school_schoolcycle_change', args=[self.cycle.pk]),
            {
                'name': self.cycle.name,
                'cycle_type': self.cycle.cycle_type,
                'start_date': self.cycle.start_date,
                'end_date': self.cycle.end_date,
                'non_school_days-TOTAL_FORMS': '1',
                'non_school_days-INITIAL_FORMS': '0',
                'non_school_days-MIN_NUM_FORMS': '0',
                'non_school_days-MAX_NUM_FORMS': '1000',
                'non_school_days-0-name': 'Asueto en línea',
                'non_school_days-0-day_type': 'ASUETO',
                'non_school_days-0-start_date': timezone.now().date().isoformat(),
                'non_school_days-0-end_date': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.cycle.non_school_days.count(), 1)
        self.assertEqual(
            self.cycle.non_school_days.first().name, 'Asueto en línea'
        )

    def test_deleting_cycle_with_courses_blocked(self) -> None:
        _, _, _, _, course = make_course_data('Grupo AdminCurso')
        response = self.client.post(
            reverse('admin:school_schoolcycle_delete', args=[course.school_cycle.pk]),
            {'post': 'yes'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'protected related objects')  # PROTECT error surfaces on the page
        self.assertTrue(
            SchoolCycle.objects.filter(pk=course.school_cycle.pk).exists()
        )

    def test_deleting_childless_cycle_removes_non_school_days(self) -> None:
        NonSchoolDay.objects.create(
            cycle=self.cycle,
            name='Día eliminable',
            day_type=NonSchoolDay.DayType.OTRO,
            start_date=timezone.now().date(),
        )
        response = self.client.post(
            reverse('admin:school_schoolcycle_delete', args=[self.cycle.pk]),
            {'post': 'yes'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SchoolCycle.objects.filter(pk=self.cycle.pk).exists())
        self.assertFalse(NonSchoolDay.objects.filter(cycle_id=self.cycle.pk).exists())

    def test_course_admin_shows_cycle(self) -> None:
        _, _, _, _, course = make_course_data('Grupo AdminFiltro')
        response = self.client.get(
            reverse('admin:school_course_change', args=[course.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ciclo escolar')
