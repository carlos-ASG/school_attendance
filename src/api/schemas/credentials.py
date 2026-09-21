from datetime import datetime
from typing import Literal
from uuid import UUID

from ninja import Schema


class DesktopStudentOut(Schema):
    id: UUID
    first_name: str
    paternal_surname: str
    maternal_surname: str
    email: str | None
    groups: list[str]
    has_photo: bool
    photo_url: str | None


class IssuedCredentialIn(Schema):
    id: UUID
    serial_number: str
    issued_at: datetime | None = None
    expiration_date: datetime | None = None
    max_expiration_date: datetime | None = None
    scan_kind: str = ''


class CredentialEventIn(Schema):
    """Evento push discriminado por operación (payload plano según contrato)."""

    operation: Literal['issued', 'revoked', 'validity_extended']
    occurred_at: datetime
    # issued
    student_id: UUID | None = None
    credential: IssuedCredentialIn | None = None
    # revoked
    credential_id: UUID | None = None
    revoked_at: datetime | None = None
    # validity_extended
    expiration_date: datetime | None = None
    max_expiration_date: datetime | None = None


class CredentialEventApplied(Schema):
    status: str
    operation: str
