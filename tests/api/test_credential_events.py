"""Tests for the /api/desktop/credential-events endpoint (validity limits)."""

from datetime import UTC
from datetime import datetime
from uuid import uuid4

import pytest

from credentials.models import Credential
from integrations.keys import extract_prefix
from integrations.keys import generate_key
from integrations.keys import hash_key
from integrations.models import DesktopApiKey
from school.models import Student

pytestmark = pytest.mark.django_db

URL = "/api/desktop/credential-events"


@pytest.fixture
def desktop_key(db):
    key = generate_key()
    DesktopApiKey.objects.create(
        name="estacion-test",
        prefix=extract_prefix(key),
        hash=hash_key(key),
    )
    return key


@pytest.fixture
def student():
    return Student.objects.create(
        first_name="Beto",
        paternal_surname="López",
        maternal_surname="Ruiz",
    )


def post_event(client, key, payload):
    return client.post(
        URL,
        payload,
        content_type="application/json",
        headers={"X-API-Key": key},
    )


def issued_payload(student_id, *, expiration, max_expiration):
    return {
        "operation": "issued",
        "occurred_at": datetime(2026, 1, 10, 12, 0, tzinfo=UTC).isoformat(),
        "credential": {
            "id": str(uuid4()),
            "serial_number": "SN-001",
            "issued_at": datetime(2026, 1, 10, 12, 0, tzinfo=UTC).isoformat(),
            "expiration_date": expiration.isoformat(),
            "max_expiration_date": (
                max_expiration.isoformat() if max_expiration else None
            ),
        },
        "student_id": str(student_id),
    }


def extended_payload(credential_id, expiration):
    return {
        "operation": "validity_extended",
        "occurred_at": datetime(2026, 2, 1, 12, 0, tzinfo=UTC).isoformat(),
        "credential_id": str(credential_id),
        "expiration_date": expiration.isoformat(),
    }


def test_validity_extended_within_max_applies(client, desktop_key, student):
    payload = issued_payload(
        student.id,
        expiration=datetime(2026, 12, 31, tzinfo=UTC),
        max_expiration=datetime(2027, 12, 31, tzinfo=UTC),
    )
    assert post_event(client, desktop_key, payload).status_code == 200

    response = post_event(
        client,
        desktop_key,
        extended_payload(
            payload["credential"]["id"],
            datetime(2027, 6, 30, tzinfo=UTC),
        ),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "applied",
        "operation": "validity_extended",
    }
    credential = Credential.objects.get(pk=payload["credential"]["id"])
    assert credential.expiration_date == datetime(
        2027,
        6,
        30,
        tzinfo=UTC,
    )
    assert credential.max_expiration_date == datetime(
        2027,
        12,
        31,
        tzinfo=UTC,
    )


def test_validity_extended_beyond_max_returns_422_and_is_noop(
    client,
    desktop_key,
    student,
):
    payload = issued_payload(
        student.id,
        expiration=datetime(2026, 12, 31, tzinfo=UTC),
        max_expiration=datetime(2027, 12, 31, tzinfo=UTC),
    )
    assert post_event(client, desktop_key, payload).status_code == 200

    response = post_event(
        client,
        desktop_key,
        extended_payload(
            payload["credential"]["id"],
            datetime(2028, 1, 1, tzinfo=UTC),
        ),
    )

    assert response.status_code == 422
    assert "expiración máxima" in response.json()["detail"]
    credential = Credential.objects.get(pk=payload["credential"]["id"])
    assert credential.expiration_date == datetime(2026, 12, 31, tzinfo=UTC)


def test_issued_beyond_max_returns_422_and_creates_nothing(
    client,
    desktop_key,
    student,
):
    payload = issued_payload(
        student.id,
        expiration=datetime(2028, 1, 1, tzinfo=UTC),
        max_expiration=datetime(2027, 12, 31, tzinfo=UTC),
    )

    response = post_event(client, desktop_key, payload)

    assert response.status_code == 422
    assert "expiración máxima" in response.json()["detail"]
    assert not Credential.objects.exists()


def test_issued_without_max_returns_422_and_creates_nothing(
    client,
    desktop_key,
    student,
):
    payload = issued_payload(
        student.id,
        expiration=datetime(2026, 12, 31, tzinfo=UTC),
        max_expiration=datetime(2027, 12, 31, tzinfo=UTC),
    )
    del payload["credential"]["max_expiration_date"]

    response = post_event(client, desktop_key, payload)

    assert response.status_code == 422
    assert not Credential.objects.exists()


def test_validity_extended_ignores_max_in_payload(
    client,
    desktop_key,
    student,
):
    """Contrato: el campo max_expiration_date del evento ya no se declara.

    Si la estación lo sigue enviando, se ignora (pydantic descarta extras)
    y max_expiration_date persistido queda con el valor del alta.
    """
    payload = issued_payload(
        student.id,
        expiration=datetime(2026, 12, 31, tzinfo=UTC),
        max_expiration=datetime(2027, 12, 31, tzinfo=UTC),
    )
    assert post_event(client, desktop_key, payload).status_code == 200

    event = extended_payload(
        payload["credential"]["id"],
        datetime(2027, 6, 30, tzinfo=UTC),
    )
    event["max_expiration_date"] = datetime(2030, 1, 1, tzinfo=UTC).isoformat()

    response = post_event(client, desktop_key, event)

    assert response.status_code == 200
    credential = Credential.objects.get(pk=payload["credential"]["id"])
    assert credential.expiration_date == datetime(2027, 6, 30, tzinfo=UTC)
    assert credential.max_expiration_date == datetime(
        2027,
        12,
        31,
        tzinfo=UTC,
    )
