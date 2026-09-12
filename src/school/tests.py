from datetime import timedelta

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone

from .admin import AttendanceRecordInline
from .models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    Student,
    StudentGroup,
    Subject,
    Teacher,
)


def make_course_data(group_name):
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
        student_group=group, teacher=teacher, subject=subject
    )
    return group, insider, outsider, teacher, course


class AttendanceRecordCleanTests(TestCase):
    def setUp(self):
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
    def setUp(self):
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


class AttendanceRecordInlineTests(TestCase):
    def setUp(self):
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
