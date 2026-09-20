import json
import uuid
from datetime import date, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from school.tests import make_cycle
from school.models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    Student,
    StudentGroup,
    Subject,
    Teacher,
    create_attendance_records,
)


def days_from_today(days: int) -> date:
    return timezone.now().date() + timedelta(days=days)


class AttendanceApiTests(TestCase):
    """Spec: attendance-api — session-cookie auth and bulk record updates."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.other_student = Student.objects.create(
            first_name='María', paternal_surname='López', maternal_surname='Díaz'
        )
        cls.group.students.add(cls.student, cls.other_student)
        cls.teacher_user = get_user_model().objects.create_user('profe1', password='pass')
        cls.other_user = get_user_model().objects.create_user('profe2', password='pass')
        cls.no_teacher_user = get_user_model().objects.create_user('sinperfil', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.other_teacher = Teacher.objects.create(
            first_name='Luis', last_name='Martínez', user=cls.other_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.other_subject = Subject.objects.create(name='Historia')
        cls.cycle = make_cycle()
        cls.course = Course.objects.create(
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject,
            school_cycle=cls.cycle,
        )
        cls.other_course = Course.objects.create(
            student_group=cls.group, teacher=cls.other_teacher, subject=cls.other_subject,
            school_cycle=cls.cycle,
        )
        cls.today_session = AttendanceSession.objects.create(
            course=cls.course, date=days_from_today(0), created_by=cls.teacher
        )
        create_attendance_records(cls.today_session)
        cls.past_session = AttendanceSession.objects.create(
            course=cls.course, date=days_from_today(-2), created_by=cls.teacher
        )
        create_attendance_records(cls.past_session)
        cls.other_teacher_session = AttendanceSession.objects.create(
            course=cls.other_course, date=days_from_today(0), created_by=cls.other_teacher
        )
        create_attendance_records(cls.other_teacher_session)

    def setUp(self) -> None:
        self.client.force_login(self.teacher_user)

    def url(self, session: AttendanceSession) -> str:
        return reverse('api:update_session_records', args=[session.pk])

    def patch(
        self, session: AttendanceSession, records: list[dict[str, Any]], **extra: Any
    ) -> HttpResponse:
        return self.client.patch(
            self.url(session),
            data=json.dumps({'records': records}),
            content_type='application/json',
            **extra,
        )

    def record(
        self, session: AttendanceSession, student: Student
    ) -> AttendanceRecord:
        return session.records.get(student=student)

    def test_teacher_updates_records(self):
        record = self.record(self.today_session, self.student)
        response = self.patch(
            self.today_session,
            [{'id': str(record.pk), 'status': 'LATE', 'notes': 'Llegó tarde'}],
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]['id'], str(record.pk))
        self.assertEqual(data[0]['status'], 'LATE')
        self.assertEqual(data[0]['notes'], 'Llegó tarde')
        record.refresh_from_db()
        self.assertEqual(record.status, 'LATE')
        self.assertEqual(record.notes, 'Llegó tarde')

    def test_notes_saved_together_with_status(self):
        record = self.record(self.today_session, self.student)
        response = self.patch(
            self.today_session,
            [{'id': str(record.pk), 'status': 'ABSENT', 'notes': 'Enfermo'}],
        )
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, 'ABSENT')
        self.assertEqual(record.notes, 'Enfermo')

    def test_invalid_status_rejected(self):
        record = self.record(self.today_session, self.student)
        response = self.patch(
            self.today_session,
            [{'id': str(record.pk), 'status': 'NOPE', 'notes': ''}],
        )
        self.assertEqual(response.status_code, 422)
        record.refresh_from_db()
        self.assertEqual(record.status, 'PRESENT')
        self.assertEqual(record.notes, '')

    def test_foreign_record_rejected_atomically(self):
        valid = self.record(self.today_session, self.student)
        foreign = self.record(self.other_teacher_session, self.student)
        response = self.patch(
            self.today_session,
            [
                {'id': str(valid.pk), 'status': 'EXCUSED', 'notes': 'x'},
                {'id': str(foreign.pk), 'status': 'EXCUSED', 'notes': 'y'},
            ],
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            [entry['id'] for entry in response.json()['detail']],
            [str(foreign.pk)],
        )
        valid.refresh_from_db()
        self.assertEqual(valid.status, 'PRESENT')
        self.assertEqual(valid.notes, '')

    def test_unknown_record_rejected(self):
        response = self.patch(
            self.today_session,
            [{'id': str(uuid.uuid4()), 'status': 'LATE', 'notes': ''}],
        )
        self.assertEqual(response.status_code, 422)

    def test_other_teacher_session_404(self):
        record = self.record(self.other_teacher_session, self.student)
        response = self.patch(
            self.other_teacher_session,
            [{'id': str(record.pk), 'status': 'LATE', 'notes': ''}],
        )
        self.assertEqual(response.status_code, 404)
        record.refresh_from_db()
        self.assertEqual(record.status, 'PRESENT')

    def test_nonexistent_session_404(self):
        response = self.patch(
            AttendanceSession(pk=uuid.uuid4()),
            [{'id': str(uuid.uuid4()), 'status': 'LATE', 'notes': ''}],
        )
        self.assertEqual(response.status_code, 404)

    def test_duplicate_entries_last_wins(self):
        record = self.record(self.today_session, self.student)
        response = self.patch(
            self.today_session,
            [
                {'id': str(record.pk), 'status': 'LATE', 'notes': 'first'},
                {'id': str(record.pk), 'status': 'ABSENT', 'notes': 'last'},
            ],
        )
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, 'ABSENT')
        self.assertEqual(record.notes, 'last')

    def test_past_session_update_allowed(self):
        record = self.record(self.past_session, self.student)
        response = self.patch(
            self.past_session,
            [{'id': str(record.pk), 'status': 'EXCUSED', 'notes': 'Corrección'}],
        )
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, 'EXCUSED')

    def test_anonymous_rejected_401(self):
        self.client.logout()
        response = self.patch(self.today_session, [])
        self.assertEqual(response.status_code, 401)

    def test_non_teacher_rejected_403(self):
        self.client.force_login(self.no_teacher_user)
        response = self.patch(self.today_session, [])
        self.assertEqual(response.status_code, 403)

    def test_csrf_required(self):
        from django.test import Client

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.teacher_user)
        response = csrf_client.patch(
            self.url(self.today_session),
            data=json.dumps({'records': []}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_empty_payload_noop(self):
        response = self.patch(self.today_session, [])
        self.assertEqual(response.status_code, 200)
