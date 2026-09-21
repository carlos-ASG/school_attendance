from datetime import datetime
from uuid import UUID

from ninja import Schema

from school.models import AttendanceRecord


class AttendanceRecordIn(Schema):
    id: UUID
    status: AttendanceRecord.Status
    notes: str


class AttendanceRecordBulkIn(Schema):
    records: list[AttendanceRecordIn]


class AttendanceRecordOut(Schema):
    id: UUID
    status: AttendanceRecord.Status
    notes: str
    updated_at: datetime


class RecordError(Schema):
    id: UUID
    error: str


class AttendanceUpdateError(Schema):
    detail: list[RecordError]
