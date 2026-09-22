import io
import shutil
import tempfile
import uuid
from datetime import date, time, timedelta
from typing import Any

import pillow_heif
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import ExifTags, Image

from .admin import AttendanceRecordInline
from .calendar import (
    get_active_cycle,
    get_non_school_day,
    session_is_frozen,
    validate_session_date,
)
from .images import (
    MAX_PHOTO_SIZE_BYTES,
    PHOTO_INVALID_ERROR,
    PHOTO_TOO_LARGE_ERROR,
    StudentPhotoField,
)
from .models import (
    AttendanceRecord,
    AttendanceSession,
    ClassSchedule,
    Course,
    NonSchoolDay,
    SchoolCycle,
    Student,
    StudentGroup,
    Subject,
    Teacher,
    create_attendance_records,
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


def add_full_week_schedule(course: Course) -> list[ClassSchedule]:
    """Create one ClassSchedule slot per weekday (07:00–08:00) for `course`.

    Makes every weekday valid for session creation so tests never depend on
    which weekday the suite runs. For schedule-specific tests, create a
    targeted single-weekday schedule instead.
    """
    return [
        ClassSchedule.objects.create(
            course=course,
            weekday=weekday,
            start_time=time(7, 0),
            end_time=time(8, 0),
        )
        for weekday in ClassSchedule.Weekday.values
    ]


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
    add_full_week_schedule(course)
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

    def test_non_scheduled_weekday_rejected(self) -> None:
        date = timezone.now().date() - timedelta(days=1)
        self.course.schedule_slots.filter(weekday=date.weekday()).delete()
        session = AttendanceSession(
            course=self.course, date=date, created_by=self.teacher
        )
        with self.assertRaises(ValidationError) as ctx:
            session.full_clean()
        self.assertIn('no tiene clase', str(ctx.exception.messages))
        self.assertFalse(
            AttendanceSession.objects.filter(course=self.course, date=date).exists()
        )

    def test_course_without_schedule_rejected(self) -> None:
        self.course.schedule_slots.all().delete()
        session = AttendanceSession(
            course=self.course,
            date=timezone.now().date() - timedelta(days=1),
            created_by=self.teacher,
        )
        with self.assertRaises(ValidationError) as ctx:
            session.full_clean()
        self.assertIn('no tiene horario asignado', str(ctx.exception.messages))

    def test_existing_session_survives_later_schedule_change(self) -> None:
        date = timezone.now().date() - timedelta(days=2)
        session = AttendanceSession(
            course=self.course, date=date, created_by=self.teacher
        )
        session.full_clean()
        session.save()
        self.course.schedule_slots.filter(weekday=date.weekday()).delete()
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
        make_cycle('Ciclo Existente')
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

    def test_validate_session_date_rejects_non_scheduled_weekday(self) -> None:
        date = timezone.now().date() - timedelta(days=1)
        self.course.schedule_slots.filter(weekday=date.weekday()).delete()
        with self.assertRaises(ValidationError) as ctx:
            validate_session_date(self.course, date)
        message = ' '.join(ctx.exception.messages)
        self.assertIn('no tiene clase los días', message)
        self.assertIn(ClassSchedule.Weekday(date.weekday()).label.lower(), message)

    def test_validate_session_date_rejects_course_without_schedule(self) -> None:
        self.course.schedule_slots.all().delete()
        date = timezone.now().date() - timedelta(days=1)
        with self.assertRaises(ValidationError) as ctx:
            validate_session_date(self.course, date)
        self.assertIn('no tiene horario asignado', str(ctx.exception.messages))


class SessionFreezeTests(TestCase):
    """Spec: attendance-tracking — attendance freeze by school cycle."""

    def setUp(self) -> None:
        today = timezone.now().date()
        _, _, _, self.teacher, self.course = make_course_data('Grupo Freeze')
        self.past_cycle = make_cycle(
            'Ciclo pasado',
            cycle_type=SchoolCycle.CycleType.QUATRIMESTRAL,
            start=today - timedelta(days=200),
            end=today - timedelta(days=110),
        )
        self.past_course = Course.objects.create(
            school_cycle=self.past_cycle,
            student_group=self.course.student_group,
            teacher=self.teacher,
            subject=self.course.subject,
        )

    def make_session(self, course: Course, days: int) -> AttendanceSession:
        return AttendanceSession.objects.create(
            course=course,
            date=timezone.now().date() + timedelta(days=days),
            created_by=self.teacher,
        )

    def test_session_in_active_cycle_is_not_frozen(self) -> None:
        session = self.make_session(self.course, -1)
        self.assertFalse(session_is_frozen(session))

    def test_session_in_past_cycle_is_frozen(self) -> None:
        session = self.make_session(self.past_course, -150)
        self.assertTrue(session_is_frozen(session))

    def test_gap_date_freezes_even_the_latest_cycle(self) -> None:
        session = self.make_session(self.course, -1)
        gap_date = self.past_cycle.end_date + timedelta(days=1)
        self.assertTrue(session_is_frozen(session, gap_date))

    def test_course_without_cycle_is_frozen(self) -> None:
        session = AttendanceSession(course=Course(), date=timezone.now().date())
        self.assertTrue(session_is_frozen(session))


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


def _two_tone_image(width: int = 1600, height: int = 800) -> Image.Image:
    image = Image.new('RGB', (width, height))
    image.paste((255, 0, 0), (0, 0, width, height // 2))
    image.paste((0, 0, 255), (0, height // 2, width, height))
    return image


def _camera_jpeg_bytes(image: Image.Image) -> bytes:
    """Un-transposed camera JPEG: pixels rotated CCW + orientation 6 + GPS EXIF."""
    exif = Image.Exif()
    exif[ExifTags.Base.Orientation] = 6
    gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps[ExifTags.GPS.GPSLatitudeRef] = 'N'
    gps[ExifTags.GPS.GPSLatitude] = (37.7749, 46.0, 22.0)
    gps[ExifTags.GPS.GPSLongitudeRef] = 'W'
    gps[ExifTags.GPS.GPSLongitude] = (122.4194, 25.0, 12.0)
    buf = io.BytesIO()
    image.transpose(Image.Transpose.ROTATE_90).save(buf, 'JPEG', exif=exif.tobytes())
    return buf.getvalue()


def _small_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new('RGB', (400, 300), (0, 128, 128)).save(buf, 'JPEG')
    return buf.getvalue()


def _assert_pixel_close(testcase: TestCase, pixel: tuple, expected: tuple) -> None:
    testcase.assertTrue(
        all(abs(actual - target) <= 3 for actual, target in zip(pixel, expected)),
        f'{pixel} not close to {expected}',
    )


_PHOTO_MEDIA_ROOT = tempfile.mkdtemp(prefix='school-photo-tests-')


def tearDownModule() -> None:
    shutil.rmtree(_PHOTO_MEDIA_ROOT, ignore_errors=True)


@override_settings(MEDIA_ROOT=_PHOTO_MEDIA_ROOT)
class StudentPhotoPipelineTests(TestCase):
    def make_student(self) -> Student:
        return Student(
            first_name='Foto', paternal_surname='Pipeline', maternal_surname='Test'
        )

    def test_camera_jpeg_normalized(self) -> None:
        student = self.make_student()
        student.photo.save(
            'camera.jpg',
            SimpleUploadedFile('camera.jpg', _camera_jpeg_bytes(_two_tone_image())),
            save=True,
        )
        self.assertTrue(student.photo.name.startswith('students/'))
        self.assertTrue(student.photo.name.endswith('.jpg'))
        stem = student.photo.name.rsplit('/', 1)[-1].removesuffix('.jpg')
        uuid.UUID(stem)
        with Image.open(student.photo.path) as stored:
            self.assertEqual(stored.format, 'JPEG')
            self.assertEqual(stored.size, (600, 300))
            _assert_pixel_close(self, stored.getpixel((300, 75)), (255, 0, 0))
            _assert_pixel_close(self, stored.getpixel((300, 225)), (0, 0, 255))
            exif = stored.getexif()
            self.assertEqual(dict(exif), {})
            self.assertEqual(dict(exif.get_ifd(ExifTags.IFD.GPSInfo)), {})

    def test_heic_normalized(self) -> None:
        student = self.make_student()
        buf = io.BytesIO()
        pillow_heif.from_pillow(Image.new('RGB', (900, 500), (0, 128, 128))).save(buf)
        student.photo.save(
            'iphone.heic', SimpleUploadedFile('iphone.heic', buf.getvalue()), save=True
        )
        with Image.open(student.photo.path) as stored:
            self.assertEqual(stored.format, 'JPEG')
            self.assertEqual(stored.size, (600, 333))
            self.assertEqual(dict(stored.getexif()), {})

    def test_webp_normalized(self) -> None:
        student = self.make_student()
        buf = io.BytesIO()
        Image.new('RGB', (800, 600), (10, 200, 30)).save(buf, 'WEBP')
        student.photo.save(
            'img.webp', SimpleUploadedFile('img.webp', buf.getvalue()), save=True
        )
        with Image.open(student.photo.path) as stored:
            self.assertEqual(stored.format, 'JPEG')
            self.assertEqual(stored.size, (600, 450))
            self.assertEqual(dict(stored.getexif()), {})

    def test_png_alpha_flattened_onto_white(self) -> None:
        student = self.make_student()
        buf = io.BytesIO()
        Image.new('RGBA', (100, 80), (255, 0, 0, 0)).save(buf, 'PNG')
        student.photo.save(
            'transparent.png', SimpleUploadedFile('transparent.png', buf.getvalue()), save=True
        )
        with Image.open(student.photo.path) as stored:
            self.assertEqual(stored.mode, 'RGB')
            self.assertEqual(stored.getpixel((0, 0)), (255, 255, 255))

    def test_small_image_not_upscaled(self) -> None:
        student = self.make_student()
        buf = io.BytesIO()
        Image.new('RGB', (300, 200), 'gray').save(buf, 'PNG')
        student.photo.save(
            'small.png', SimpleUploadedFile('small.png', buf.getvalue()), save=True
        )
        with Image.open(student.photo.path) as stored:
            self.assertEqual(stored.size, (300, 200))

    def test_undecodable_rejected_with_spanish_error(self) -> None:
        field = StudentPhotoField()
        with self.assertRaises(ValidationError) as ctx:
            field.to_python(SimpleUploadedFile('photo.jpg', b'esto no es una imagen'))
        self.assertIn(PHOTO_INVALID_ERROR, str(ctx.exception.messages))
        storage = Student._meta.get_field('photo').storage
        with self.assertRaises(ValidationError) as ctx:
            storage._save('students/x.jpg', ContentFile(b'esto no es una imagen'))
        self.assertIn(PHOTO_INVALID_ERROR, str(ctx.exception.messages))

    def test_oversized_rejected_before_decode(self) -> None:
        field = StudentPhotoField()
        payload = b'x' * (MAX_PHOTO_SIZE_BYTES + 1)
        with self.assertRaises(ValidationError) as ctx:
            field.to_python(SimpleUploadedFile('photo.jpg', payload))
        self.assertIn(PHOTO_TOO_LARGE_ERROR, str(ctx.exception.messages))
        storage = Student._meta.get_field('photo').storage
        with self.assertRaises(ValidationError) as ctx:
            storage._save('students/x.jpg', ContentFile(payload))
        self.assertIn(PHOTO_TOO_LARGE_ERROR, str(ctx.exception.messages))

    def test_replacement_deletes_previous_file(self) -> None:
        student = self.make_student()
        student.photo.save(
            'a.jpg', SimpleUploadedFile('a.jpg', _small_jpeg_bytes()), save=True
        )
        original_name = student.photo.name
        files_before = set(student.photo.storage.listdir('students')[1])
        buf = io.BytesIO()
        Image.new('RGB', (500, 400), 'purple').save(buf, 'JPEG')
        student.photo.save(
            'b.jpg', SimpleUploadedFile('b.jpg', buf.getvalue()), save=True
        )
        storage = student.photo.storage
        self.assertFalse(storage.exists(original_name))
        self.assertTrue(storage.exists(student.photo.name))
        files_after = set(storage.listdir('students')[1])
        self.assertEqual(files_after - files_before, {student.photo.name.rsplit('/', 1)[-1]})
        self.assertNotIn(original_name.rsplit('/', 1)[-1], files_after)
@override_settings(MEDIA_ROOT=_PHOTO_MEDIA_ROOT)
class StudentPhotoAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = get_user_model().objects.create_superuser(
            'photo-admin', 'photo-admin@example.com', 'pass'
        )
        cls.student = Student.objects.create(
            first_name='Nora', paternal_surname='Ruiz', maternal_surname='Vega'
        )

    def setUp(self) -> None:
        self.client.force_login(self.admin_user)

    def change_url(self) -> str:
        return reverse('admin:school_student_change', args=[self.student.pk])

    def test_upload_via_change_form_stores_one_normalized_file(self) -> None:
        response = self.client.post(
            self.change_url(),
            {
                'first_name': self.student.first_name,
                'paternal_surname': self.student.paternal_surname,
                'maternal_surname': self.student.maternal_surname,
                'email': '',
                'photo': SimpleUploadedFile(
                    'camera.jpg', _camera_jpeg_bytes(_two_tone_image())
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertTrue(self.student.photo)
        with Image.open(self.student.photo.path) as stored:
            self.assertEqual(stored.format, 'JPEG')
            self.assertEqual(stored.size, (600, 300))
            self.assertEqual(dict(stored.getexif()), {})
        self.assertEqual(len(self.student.photo.storage.listdir('students')[1]), 1)

    def test_save_without_photo_succeeds(self) -> None:
        response = self.client.post(
            self.change_url(),
            {
                'first_name': 'Sin',
                'paternal_surname': 'Foto',
                'maternal_surname': 'Ninguna',
                'email': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertFalse(self.student.photo)


class TeacherPanelPhotoExclusionTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Foto')
        cls.student = Student.objects.create(
            first_name='Ana', paternal_surname='Pérez', maternal_surname='López'
        )
        cls.student.photo.save(
            'p.jpg', SimpleUploadedFile('p.jpg', _small_jpeg_bytes()), save=True
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = get_user_model().objects.create_user(
            'profe-foto', password='pass'
        )
        cls.teacher = Teacher.objects.create(
            first_name='Marta', last_name='López', user=cls.teacher_user
        )
        subject = Subject.objects.create(name='Materia Foto')
        cls.course = Course.objects.create(
            student_group=cls.group,
            teacher=cls.teacher,
            subject=subject,
            school_cycle=make_cycle('Ciclo Foto'),
        )
        cls.session = AttendanceSession.objects.create(
            course=cls.course,
            date=timezone.now().date() - timedelta(days=1),
            created_by=cls.teacher,
        )
        create_attendance_records(cls.session)

    def setUp(self) -> None:
        self.client.force_login(self.teacher_user)

    def assert_no_photo_references(self, url: str, must_contain: str | None = None) -> None:
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        if must_contain:
            self.assertContains(response, must_contain)
        self.assertNotContains(response, '/media/')

    def test_dashboard_has_no_photo_references(self) -> None:
        self.assert_no_photo_references(reverse('teacher_panel:dashboard'))

    def test_course_detail_has_no_photo_references(self) -> None:
        self.assert_no_photo_references(
            reverse('teacher_panel:course_detail', args=[self.course.pk]), 'Pérez'
        )

    def test_session_detail_has_no_photo_references(self) -> None:
        self.assert_no_photo_references(
            reverse('teacher_panel:session_detail', args=[self.session.pk]), 'Pérez'
        )
