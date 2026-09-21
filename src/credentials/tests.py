import uuid
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from school.models import Student

from .models import Credential, StudentCredential


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
