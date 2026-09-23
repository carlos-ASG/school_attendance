import uuid

from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from school.models import AttendanceRecord, AttendanceSession

from ..schemas import (
    AttendanceRecordBulkIn,
    AttendanceRecordOut,
    AttendanceUpdateError,
    RecordError,
)

router = Router()


@router.patch(
    '/sessions/{session_id}/records',
    response={200: list[AttendanceRecordOut], 422: AttendanceUpdateError},
)
def update_session_records(
    request: HttpRequest, session_id: uuid.UUID, payload: AttendanceRecordBulkIn
) -> list[AttendanceRecordOut] | tuple[int, AttendanceUpdateError]:
    session = (
        AttendanceSession.objects.select_related('course__school_cycle')
        .filter(pk=session_id, course__teacher=request.auth)
        .first()
    )
    if session is None:
        raise HttpError(404, 'Sesión no encontrada.')
    if session.is_frozen():
        raise HttpError(422, AttendanceSession.FROZEN_MESSAGE)

    entries = {entry.id: entry for entry in payload.records}
    found = {
        record.id: record
        for record in AttendanceRecord.objects.filter(session=session, pk__in=entries)
    }
    errors = [
        RecordError(id=record_id, error='No pertenece a la sesión indicada.')
        for record_id in entries
        if record_id not in found
    ]
    if errors:
        return 422, AttendanceUpdateError(detail=errors)

    now = timezone.now()
    records = []
    for record_id, entry in entries.items():
        record = found[record_id]
        record.status = entry.status
        record.notes = entry.notes
        record.updated_at = now
        records.append(record)

    with transaction.atomic():
        AttendanceRecord.objects.bulk_update(records, ['status', 'notes', 'updated_at'])

    return [AttendanceRecordOut.model_validate(record) for record in records]
