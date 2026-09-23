from datetime import datetime
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from school.selectors import get_student

from .models import Credential, StudentCredential


class StudentNotFound(ValidationError):
    """El evento issued referencia un estudiante inexistente."""


class CredentialNotFound(ValidationError):
    """El evento referencia una credencial inexistente."""


class ExpirationBeyondMax(ValidationError):
    """La vigencia pretendida excede la expiración máxima de la credencial."""


class MaxExpirationRequired(ValidationError):
    """El evento issued no trae max_expiration_date (techo obligatorio)."""


def _validate_vigencia(
    *, expiration_date: datetime | None, max_expiration_date: datetime | None
) -> None:
    if (
        expiration_date is not None
        and max_expiration_date is not None
        and expiration_date > max_expiration_date
    ):
        raise ExpirationBeyondMax(
            'La vigencia excede la expiración máxima de la credencial.'
        )


@transaction.atomic
def credential_issue(
    *, student_id: UUID, credential: dict[str, object]
) -> None:
    """Upsert de la credencial y vínculo con el estudiante, en una transacción.

    Idempotente: reenviar el mismo evento no crea filas extra. Si el
    estudiante o la credencial ya tienen otra relación activa, se cierra
    (historial preservado) y la activa pasa a ser esta.
    """
    now = timezone.now()
    max_expiration = credential['max_expiration_date']
    if max_expiration is None:
        raise MaxExpirationRequired(
            'La credencial requiere max_expiration_date.'
        )
    _validate_vigencia(
        expiration_date=credential['expiration_date'],
        max_expiration_date=max_expiration,
    )
    student = get_student(student_id=student_id)
    if student is None:
        raise StudentNotFound('Estudiante no encontrado.')
    credential_row, _ = Credential.objects.update_or_create(
        id=credential['id'],
        defaults={
            'serial_number': credential['serial_number'],
            'issued_at': credential['issued_at'],
            'expiration_date': credential['expiration_date'],
            'max_expiration_date': credential['max_expiration_date'],
            'synced_at': now,
        },
    )
    already_active = StudentCredential.objects.filter(
        student=student, credential=credential_row, unlinked_at__isnull=True
    ).exists()
    if not already_active:
        StudentCredential.objects.filter(
            Q(student=student) | Q(credential=credential_row),
            unlinked_at__isnull=True,
        ).update(unlinked_at=now)
        StudentCredential.objects.create(
            student=student, credential=credential_row, linked_at=now
        )


@transaction.atomic
def credential_revoke(*, credential_id: UUID, revoked_at: datetime) -> None:
    now = timezone.now()
    try:
        credential = Credential.objects.select_for_update().get(pk=credential_id)
    except Credential.DoesNotExist:
        raise CredentialNotFound('Credencial no encontrada.') from None
    credential.revoked_at = revoked_at
    credential.synced_at = now
    credential.save(update_fields=['revoked_at', 'synced_at'])
    StudentCredential.objects.filter(
        credential=credential, unlinked_at__isnull=True
    ).update(unlinked_at=now)


@transaction.atomic
def credential_extend_validity(
    *,
    credential_id: UUID,
    expiration_date: datetime,
) -> None:
    """Actualiza `expiration_date` dentro del techo `max_expiration_date`.

    `max_expiration_date` es inmutable tras el alta: solo delimita la
    extensión. Extender más allá del techo lanza `ExpirationBeyondMax`.
    """
    now = timezone.now()
    try:
        credential = Credential.objects.select_for_update().get(pk=credential_id)
    except Credential.DoesNotExist:
        raise CredentialNotFound('Credencial no encontrada.') from None
    _validate_vigencia(
        expiration_date=expiration_date,
        max_expiration_date=credential.max_expiration_date,
    )
    credential.expiration_date = expiration_date
    credential.synced_at = now
    credential.save(update_fields=['expiration_date', 'synced_at'])
