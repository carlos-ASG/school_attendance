import io
import json
import tempfile
import uuid
from datetime import date, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from credentials.models import Credential, StudentCredential
from integrations.keys import extract_prefix, generate_key, hash_key
from integrations.models import DesktopApiKey
from school.models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    SchoolCycle,
    Student,
    StudentGroup,
    Subject,
    Teacher,
)
from school.services import create_attendance_records
from school.tests import make_cycle


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
        cls.past_cycle = make_cycle(
            'Ciclo pasado',
            cycle_type=SchoolCycle.CycleType.QUATRIMESTRAL,
            start=days_from_today(-200),
            end=days_from_today(-110),
        )
        cls.past_course = Course.objects.create(
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject,
            school_cycle=cls.past_cycle,
        )
        cls.frozen_session = AttendanceSession.objects.create(
            course=cls.past_course, date=days_from_today(-150), created_by=cls.teacher
        )
        create_attendance_records(cls.frozen_session)

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

    def test_frozen_session_update_rejected(self):
        record = self.record(self.frozen_session, self.student)
        response = self.patch(
            self.frozen_session,
            [{'id': str(record.pk), 'status': 'LATE', 'notes': 'No debería guardarse'}],
        )
        self.assertEqual(response.status_code, 422)
        record.refresh_from_db()
        self.assertEqual(record.status, 'PRESENT')
        self.assertEqual(record.notes, '')

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


_DESKTOP_MEDIA_ROOT = tempfile.mkdtemp(prefix='api-desktop-photos-')


@override_settings(MEDIA_ROOT=_DESKTOP_MEDIA_ROOT)
class DesktopApiTests(TestCase):
    """Spec: desktop-integration-api + desktop-api-auth — key auth and roster."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo A')
        cls.other_group = StudentGroup.objects.create(name='Grupo B')
        cls.student = Student.objects.create(
            first_name='Juan',
            paternal_surname='Pérez',
            maternal_surname='Gómez',
            email='juan@example.com',
        )
        cls.other_student = Student.objects.create(
            first_name='María', paternal_surname='López', maternal_surname='Díaz'
        )
        cls.group.students.add(cls.student, cls.other_student)
        cls.other_group.students.add(cls.student)
        cls.raw_key = generate_key()
        cls.api_key = DesktopApiKey.objects.create(
            name='estacion-test',
            prefix=extract_prefix(cls.raw_key),
            hash=hash_key(cls.raw_key),
        )

    @staticmethod
    def _jpeg_bytes() -> bytes:
        buf = io.BytesIO()
        Image.new('RGB', (8, 8), 'blue').save(buf, format='JPEG')
        return buf.getvalue()

    def setUp(self) -> None:
        self.headers = {'HTTP_X_API_KEY': self.raw_key}

    def get(self, path: str, **kwargs: Any) -> HttpResponse:
        return self.client.get(path, **self.headers, **kwargs)

    def test_valid_key_allows_access(self) -> None:
        response = self.get('/api/desktop/students')
        self.assertEqual(response.status_code, 200)

    def test_missing_invalid_and_revoked_keys_same_generic_401(self) -> None:
        missing = self.client.get('/api/desktop/students')
        invalid = self.client.get(
            '/api/desktop/students', HTTP_X_API_KEY='dsk_' + 'z' * 43
        )
        key = generate_key()
        DesktopApiKey.objects.create(
            name='estacion-revocada',
            prefix=extract_prefix(key),
            hash=hash_key(key),
            revoked_at=timezone.now(),
        )
        revoked = self.client.get('/api/desktop/students', HTTP_X_API_KEY=key)
        for response in (missing, invalid, revoked):
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.content, missing.content)

    def test_roster_returns_all_students_with_groups_and_photo_flags(self) -> None:
        self.student.photo.save(
            'foto.jpg', SimpleUploadedFile('foto.jpg', self._jpeg_bytes()), save=True
        )
        response = self.get('/api/desktop/students')
        self.assertEqual(response.status_code, 200)
        by_id = {entry['id']: entry for entry in response.json()}
        self.assertEqual(len(by_id), 2)
        plain = by_id[str(self.other_student.pk)]
        self.assertEqual(plain['first_name'], 'María')
        self.assertEqual(plain['paternal_surname'], 'López')
        self.assertEqual(plain['maternal_surname'], 'Díaz')
        self.assertIsNone(plain['email'])
        self.assertEqual(plain['groups'], ['Grupo A'])
        self.assertFalse(plain['has_photo'])
        self.assertIsNone(plain['photo_url'])
        rich = by_id[str(self.student.pk)]
        self.assertEqual(rich['email'], 'juan@example.com')
        self.assertEqual(rich['groups'], ['Grupo A', 'Grupo B'])
        self.assertTrue(rich['has_photo'])
        self.assertEqual(
            rich['photo_url'],
            f'/api/desktop/students/{self.student.pk}/photo',
        )

    def test_photo_download_returns_jpeg_bytes(self) -> None:
        self.other_student.photo.save(
            'foto.jpg', SimpleUploadedFile('foto.jpg', self._jpeg_bytes()), save=True
        )
        expected = self.other_student.photo.read()
        response = self.get(f'/api/desktop/students/{self.other_student.pk}/photo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(response.content, expected)

    def test_photo_of_student_without_photo_404(self) -> None:
        response = self.get(f'/api/desktop/students/{self.student.pk}/photo')
        self.assertEqual(response.status_code, 404)

    def test_photo_of_unknown_student_404(self) -> None:
        response = self.get(f'/api/desktop/students/{uuid.uuid4()}/photo')
        self.assertEqual(response.status_code, 404)


def issued_payload(credential_id: uuid.UUID, student_id: uuid.UUID) -> dict[str, Any]:
    return {
        'operation': 'issued',
        'occurred_at': '2026-09-21T12:00:00Z',
        'student_id': str(student_id),
        'credential': {
            'id': str(credential_id),
            'serial_number': 'SN-100',
            'issued_at': '2026-01-15T10:30:00Z',
            'expiration_date': '2027-12-31T23:59:59Z',
            'max_expiration_date': None,
            'scan_kind': 'QR',
        },
    }


class CredentialEventsApiTests(TestCase):
    """Spec: desktop-integration-api — push events (issued/revoked/extended)."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.raw_key = generate_key()
        cls.api_key = DesktopApiKey.objects.create(
            name='estacion-eventos',
            prefix=extract_prefix(cls.raw_key),
            hash=hash_key(cls.raw_key),
        )

    def setUp(self) -> None:
        self.headers = {'HTTP_X_API_KEY': self.raw_key}

    def post_event(self, payload: dict[str, Any]) -> HttpResponse:
        return self.client.post(
            '/api/desktop/credential-events',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_API_KEY=self.raw_key,
        )

    def test_issued_creates_credential_and_active_relation(self) -> None:
        credential_id = uuid.uuid4()
        response = self.post_event(issued_payload(credential_id, self.student.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'applied', 'operation': 'issued'})
        credential = Credential.objects.get(id=credential_id)
        self.assertEqual(credential.serial_number, 'SN-100')
        self.assertEqual(credential.scan_kind, 'QR')
        self.assertEqual(credential.status, Credential.Status.ACTIVE)
        relation = StudentCredential.objects.get(credential_id=credential_id)
        self.assertEqual(relation.student, self.student)
        self.assertIsNone(relation.unlinked_at)
        self.assertIsNotNone(relation.linked_at)

    def test_reissue_closes_previous_relation(self) -> None:
        first_id, second_id = uuid.uuid4(), uuid.uuid4()
        self.post_event(issued_payload(first_id, self.student.pk))
        self.post_event(issued_payload(second_id, self.student.pk))
        closed = StudentCredential.objects.get(credential_id=first_id)
        active = StudentCredential.objects.get(credential_id=second_id)
        self.assertIsNotNone(closed.unlinked_at)
        self.assertIsNone(active.unlinked_at)
        self.assertEqual(
            StudentCredential.objects.filter(student=self.student).count(), 2
        )

    def test_issued_resend_is_idempotent(self) -> None:
        credential_id = uuid.uuid4()
        payload = issued_payload(credential_id, self.student.pk)
        self.post_event(payload)
        self.post_event(payload)
        self.assertEqual(Credential.objects.count(), 1)
        self.assertEqual(
            StudentCredential.objects.filter(student=self.student).count(), 1
        )
        relation = StudentCredential.objects.get()
        self.assertIsNone(relation.unlinked_at)

    def test_revoked_updates_mirror_and_closes_relation(self) -> None:
        credential_id = uuid.uuid4()
        self.post_event(issued_payload(credential_id, self.student.pk))
        revoked_at = '2026-09-20T08:00:00Z'
        response = self.post_event(
            {
                'operation': 'revoked',
                'occurred_at': '2026-09-20T08:05:00Z',
                'credential_id': str(credential_id),
                'revoked_at': revoked_at,
            }
        )
        self.assertEqual(response.status_code, 200)
        credential = Credential.objects.get(id=credential_id)
        self.assertEqual(credential.status, Credential.Status.REVOKED)
        relation = StudentCredential.objects.get(credential_id=credential_id)
        self.assertIsNotNone(relation.unlinked_at)

    def test_validity_extended_updates_mirror(self) -> None:
        credential_id = uuid.uuid4()
        self.post_event(issued_payload(credential_id, self.student.pk))
        response = self.post_event(
            {
                'operation': 'validity_extended',
                'occurred_at': '2026-09-20T08:10:00Z',
                'credential_id': str(credential_id),
                'expiration_date': '2028-06-30T23:59:59Z',
                'max_expiration_date': '2029-06-30T23:59:59Z',
            }
        )
        self.assertEqual(response.status_code, 200)
        credential = Credential.objects.get(id=credential_id)
        self.assertEqual(credential.expiration_date.year, 2028)
        self.assertEqual(credential.max_expiration_date.year, 2029)

    def test_revoked_unknown_credential_404(self) -> None:
        response = self.post_event(
            {
                'operation': 'revoked',
                'occurred_at': '2026-09-20T08:00:00Z',
                'credential_id': str(uuid.uuid4()),
                'revoked_at': '2026-09-20T08:00:00Z',
            }
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Credential.objects.count(), 0)

    def test_validity_extended_unknown_credential_404(self) -> None:
        response = self.post_event(
            {
                'operation': 'validity_extended',
                'occurred_at': '2026-09-20T08:00:00Z',
                'credential_id': str(uuid.uuid4()),
                'expiration_date': '2028-06-30T23:59:59Z',
                'max_expiration_date': None,
            }
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Credential.objects.count(), 0)

    def test_invalid_operation_rejected_422(self) -> None:
        payload = issued_payload(uuid.uuid4(), self.student.pk)
        payload['operation'] = 'deleted'
        response = self.post_event(payload)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Credential.objects.count(), 0)

    def test_issued_unknown_student_422_and_persists_nothing(self) -> None:
        response = self.post_event(issued_payload(uuid.uuid4(), uuid.uuid4()))
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Credential.objects.count(), 0)
        self.assertEqual(StudentCredential.objects.count(), 0)

    def test_events_require_api_key(self) -> None:
        response = self.client.post(
            '/api/desktop/credential-events',
            data=json.dumps(issued_payload(uuid.uuid4(), self.student.pk)),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
