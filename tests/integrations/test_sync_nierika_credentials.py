"""Tests for the sync_nierika_credentials management command."""

from datetime import UTC
from datetime import datetime
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.management import call_command

from credentials.models import Credential

pytestmark = pytest.mark.django_db


def sync_fields(**overrides):
    fields = {
        "id": uuid4(),
        "serial_number": "SN-001",
        "issued_at": None,
        "expiration_date": None,
        "max_expiration_date": datetime(2027, 12, 31, tzinfo=UTC),
        "revoked_at": None,
    }
    fields.update(overrides)
    return fields


def run_sync(settings, *, credentials):
    out, err = StringIO(), StringIO()
    with patch(
        "integrations.management.commands.sync_nierika_credentials.NierikaClient",
    ) as client_class:
        client_class.return_value.iter_credentials.return_value = iter(
            credentials,
        )
        call_command("sync_nierika_credentials", stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


def test_sync_skips_rows_without_max_expiration(settings):
    settings.NIERIKA_API_BASE_URL = "https://nierika.example"
    settings.NIERIKA_API_KEY = "nkb_test"

    out, err = run_sync(
        settings,
        credentials=[
            sync_fields(serial_number="SN-OK"),
            sync_fields(
                serial_number="SN-NO-MAX",
                max_expiration_date=None,
            ),
        ],
    )

    assert Credential.objects.count() == 1
    assert Credential.objects.get().serial_number == "SN-OK"
    assert "SN-NO-MAX" in err
    assert "Skipped 1" in out
