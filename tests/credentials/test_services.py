"""Tests for credentials.services (write services)."""

from datetime import UTC
from datetime import datetime
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError

from credentials import services
from credentials.models import Credential
from credentials.models import StudentCredential
from school.models import Student

pytestmark = pytest.mark.django_db


def credential_payload(credential_id=None):
    return {
        "id": credential_id or uuid4(),
        "serial_number": "SN-001",
        "issued_at": datetime(2026, 1, 10, 12, 0, tzinfo=UTC),
        "expiration_date": datetime(2026, 12, 31, 23, 59, tzinfo=UTC),
        "max_expiration_date": datetime(2027, 12, 31, 23, 59, tzinfo=UTC),
    }


@pytest.fixture
def student(db):
    return Student.objects.create(
        first_name="Beto",
        paternal_surname="López",
        maternal_surname="Ruiz",
    )


def test_credential_issue_creates_credential_and_active_link(student):
    payload = credential_payload()

    services.credential_issue(student_id=student.id, credential=payload)

    credential = Credential.objects.get(pk=payload["id"])
    assert credential.serial_number == "SN-001"
    assert credential.synced_at is not None
    link = StudentCredential.objects.get(credential=credential)
    assert link.student == student
    assert link.linked_at is not None
    assert link.unlinked_at is None


def test_credential_issue_is_idempotent(student):
    payload = credential_payload()
    services.credential_issue(student_id=student.id, credential=payload)

    services.credential_issue(student_id=student.id, credential=payload)

    assert Credential.objects.count() == 1
    assert StudentCredential.objects.count() == 1
    assert StudentCredential.objects.filter(unlinked_at__isnull=True).count() == 1


def test_credential_issue_closes_previous_active_link(student):
    first = credential_payload()
    services.credential_issue(student_id=student.id, credential=first)

    second = credential_payload()
    services.credential_issue(student_id=student.id, credential=second)

    assert not StudentCredential.objects.filter(
        credential_id=first["id"],
        unlinked_at__isnull=True,
    ).exists()
    assert StudentCredential.objects.filter(
        credential_id=second["id"],
        unlinked_at__isnull=True,
    ).exists()


def test_credential_issue_unknown_student_creates_nothing(student):
    payload = credential_payload()

    with pytest.raises(ValidationError, match="Estudiante no encontrado"):
        services.credential_issue(student_id=uuid4(), credential=payload)

    assert not Credential.objects.exists()
    assert not StudentCredential.objects.exists()


def test_credential_issue_beyond_max_raises_and_creates_nothing(student):
    payload = credential_payload()
    payload["expiration_date"] = datetime(2028, 1, 1, tzinfo=UTC)
    payload["max_expiration_date"] = datetime(2027, 12, 31, 23, 59, tzinfo=UTC)

    with pytest.raises(ValidationError, match="expiración máxima"):
        services.credential_issue(student_id=student.id, credential=payload)

    assert not Credential.objects.exists()
    assert not StudentCredential.objects.exists()


def test_credential_issue_without_max_raises_and_creates_nothing(student):
    payload = credential_payload()
    payload["max_expiration_date"] = None

    with pytest.raises(ValidationError, match="max_expiration_date"):
        services.credential_issue(student_id=student.id, credential=payload)

    assert not Credential.objects.exists()
    assert not StudentCredential.objects.exists()


def test_credential_revoke_sets_revoked_and_closes_active_link(student):
    payload = credential_payload()
    services.credential_issue(student_id=student.id, credential=payload)
    revoked_at = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)

    services.credential_revoke(credential_id=payload["id"], revoked_at=revoked_at)

    credential = Credential.objects.get(pk=payload["id"])
    assert credential.revoked_at == revoked_at
    assert credential.synced_at is not None
    assert not StudentCredential.objects.filter(unlinked_at__isnull=True).exists()


def test_credential_revoke_unknown_credential_raises():
    with pytest.raises(ValidationError, match="Credencial no encontrada"):
        services.credential_revoke(
            credential_id=uuid4(),
            revoked_at=datetime(2026, 2, 1, 10, 0, tzinfo=UTC),
        )


def test_credential_extend_validity_updates_expiration_only(student):
    payload = credential_payload()
    services.credential_issue(student_id=student.id, credential=payload)
    expiration = datetime(2027, 6, 30, tzinfo=UTC)

    services.credential_extend_validity(
        credential_id=payload["id"],
        expiration_date=expiration,
    )

    credential = Credential.objects.get(pk=payload["id"])
    assert credential.expiration_date == expiration
    assert credential.max_expiration_date == payload["max_expiration_date"]
    assert credential.synced_at is not None


def test_credential_extend_validity_beyond_max_raises_and_is_noop(student):
    payload = credential_payload()
    services.credential_issue(student_id=student.id, credential=payload)

    with pytest.raises(ValidationError, match="expiración máxima"):
        services.credential_extend_validity(
            credential_id=payload["id"],
            expiration_date=datetime(2028, 1, 1, tzinfo=UTC),
        )

    credential = Credential.objects.get(pk=payload["id"])
    assert credential.expiration_date == payload["expiration_date"]
    assert credential.max_expiration_date == payload["max_expiration_date"]


def test_credential_extend_validity_unknown_credential_raises():
    with pytest.raises(ValidationError, match="Credencial no encontrada"):
        services.credential_extend_validity(
            credential_id=uuid4(),
            expiration_date=datetime(2027, 6, 30, tzinfo=UTC),
        )
