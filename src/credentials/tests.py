import uuid
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from school.models import Student

from .models import Credential, StudentCredential
from .services import (
    CredentialNotFound,
    StudentNotFound,
    credential_extend_validity,
    credential_issue,
    credential_revoke,
)


def make_student(first_name: str = 'Juan') -> Student:
    return Student.objects.create(
        first_name=first_name, paternal_surname='Pérez', maternal_surname='Gómez'
    )


def make_credential(
    *,
    revoked_at=None,
    expiration_date=None,
) -> Credential:
    return Credential.objects.create(
        id=uuid.uuid4(),
        serial_number=f'SN-{uuid.uuid4().hex[:10]}',
        issued_at=timezone.now(),
        expiration_date=expiration_date,
        revoked_at=revoked_at,
        synced_at=timezone.now(),
    )


class CredentialStatusTests(TestCase):
    def test_active_without_revocation_and_future_expiration(self) -> None:
        credential = make_credential(
            expiration_date=timezone.now() + timedelta(days=30)
        )
        self.assertEqual(credential.status, Credential.Status.ACTIVE)

    def test_active_without_expiration(self) -> None:
        credential = make_credential()
        self.assertEqual(credential.status, Credential.Status.ACTIVE)

    def test_expired_when_expiration_past(self) -> None:
        credential = make_credential(
            expiration_date=timezone.now() - timedelta(days=1)
        )
        self.assertEqual(credential.status, Credential.Status.EXPIRED)

    def test_revoked_takes_precedence_over_expired(self) -> None:
        credential = make_credential(
            revoked_at=timezone.now(),
            expiration_date=timezone.now() - timedelta(days=1),
        )
        self.assertEqual(credential.status, Credential.Status.REVOKED)

    def test_revoked_takes_precedence_over_active(self) -> None:
        credential = make_credential(
            revoked_at=timezone.now(),
            expiration_date=timezone.now() + timedelta(days=30),
        )
        self.assertEqual(credential.status, Credential.Status.REVOKED)


class StudentCredentialTests(TestCase):
    def setUp(self) -> None:
        self.student = make_student()
        self.credential = make_credential()

    def test_credential_cannot_have_two_relations(self) -> None:
        StudentCredential.objects.create(
            student=self.student, credential=self.credential, linked_at=timezone.now()
        )
        other_student = make_student(first_name='Sofía')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StudentCredential.objects.create(
                    student=other_student,
                    credential=self.credential,
                    linked_at=timezone.now(),
                )

    def test_student_cannot_have_two_active_relations(self) -> None:
        StudentCredential.objects.create(
            student=self.student, credential=self.credential, linked_at=timezone.now()
        )
        second_credential = make_credential()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StudentCredential.objects.create(
                    student=self.student,
                    credential=second_credential,
                    linked_at=timezone.now(),
                )

    def test_student_can_link_again_after_closing_previous_relation(self) -> None:
        StudentCredential.objects.create(
            student=self.student, credential=self.credential, linked_at=timezone.now()
        )
        StudentCredential.objects.update(unlinked_at=timezone.now())
        second_credential = make_credential()
        StudentCredential.objects.create(
            student=self.student,
            credential=second_credential,
            linked_at=timezone.now(),
        )
        active = StudentCredential.objects.filter(
            student=self.student, unlinked_at__isnull=True
        )
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.get().credential, second_credential)
        self.assertEqual(
            StudentCredential.objects.filter(student=self.student).count(), 2
        )


class CredentialServiceTests(TestCase):
    def setUp(self) -> None:
        self.student = make_student()

    def issued_data(self, credential_id: uuid.UUID | None = None) -> dict:
        return {
            'id': credential_id or uuid.uuid4(),
            'serial_number': f'SN-{uuid.uuid4().hex[:10]}',
            'issued_at': timezone.now(),
            'expiration_date': None,
            'max_expiration_date': None,
            'scan_kind': 'QR',
        }

    def test_issue_unknown_student_raises_and_persists_nothing(self) -> None:
        with self.assertRaises(StudentNotFound):
            credential_issue(student_id=uuid.uuid4(), credential=self.issued_data())
        self.assertEqual(Credential.objects.count(), 0)
        self.assertEqual(StudentCredential.objects.count(), 0)

    def test_issue_creates_credential_and_active_relation(self) -> None:
        data = self.issued_data()
        credential_issue(student_id=self.student.pk, credential=data)
        credential = Credential.objects.get(pk=data['id'])
        self.assertEqual(credential.scan_kind, 'QR')
        self.assertEqual(credential.status, Credential.Status.ACTIVE)
        relation = StudentCredential.objects.get(credential_id=data['id'])
        self.assertEqual(relation.student, self.student)
        self.assertIsNone(relation.unlinked_at)

    def test_issue_resend_is_idempotent(self) -> None:
        data = self.issued_data()
        credential_issue(student_id=self.student.pk, credential=data)
        credential_issue(student_id=self.student.pk, credential=data)
        self.assertEqual(Credential.objects.count(), 1)
        self.assertEqual(StudentCredential.objects.count(), 1)
        self.assertIsNone(StudentCredential.objects.get().unlinked_at)

    def test_issue_closes_previous_relation(self) -> None:
        first, second = self.issued_data(), self.issued_data()
        credential_issue(student_id=self.student.pk, credential=first)
        credential_issue(student_id=self.student.pk, credential=second)
        self.assertEqual(StudentCredential.objects.count(), 2)
        closed = StudentCredential.objects.get(credential_id=first['id'])
        active = StudentCredential.objects.get(credential_id=second['id'])
        self.assertIsNotNone(closed.unlinked_at)
        self.assertIsNone(active.unlinked_at)

    def test_revoke_unknown_credential_raises(self) -> None:
        with self.assertRaises(CredentialNotFound):
            credential_revoke(
                credential_id=uuid.uuid4(), revoked_at=timezone.now()
            )

    def test_revoke_updates_mirror_and_closes_relation(self) -> None:
        data = self.issued_data()
        credential_issue(student_id=self.student.pk, credential=data)
        revoked_at = timezone.now()
        credential_revoke(credential_id=data['id'], revoked_at=revoked_at)
        credential = Credential.objects.get(pk=data['id'])
        self.assertEqual(credential.revoked_at, revoked_at)
        self.assertEqual(credential.status, Credential.Status.REVOKED)
        self.assertIsNotNone(
            StudentCredential.objects.get(credential_id=data['id']).unlinked_at
        )

    def test_extend_validity_unknown_credential_raises(self) -> None:
        with self.assertRaises(CredentialNotFound):
            credential_extend_validity(
                credential_id=uuid.uuid4(),
                expiration_date=timezone.now(),
                max_expiration_date=None,
            )

    def test_extend_validity_updates_mirror(self) -> None:
        data = self.issued_data()
        credential_issue(student_id=self.student.pk, credential=data)
        expiration = timezone.now() + timedelta(days=30)
        credential_extend_validity(
            credential_id=data['id'],
            expiration_date=expiration,
            max_expiration_date=None,
        )
        credential = Credential.objects.get(pk=data['id'])
        self.assertEqual(credential.expiration_date, expiration)
        self.assertIsNone(credential.max_expiration_date)
