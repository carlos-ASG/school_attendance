from datetime import datetime

from ninja import Schema

from school.models import AttendanceRecord


class AttendanceRecordIn(Schema):
    id: int
    status: AttendanceRecord.Status
    notes: str


class AttendanceRecordBulkIn(Schema):
    records: list[AttendanceRecordIn]


class AttendanceRecordOut(Schema):
    id: int
    status: AttendanceRecord.Status
    notes: str
    updated_at: datetime


class RecordError(Schema):
    id: int
    error: str


class AttendanceUpdateError(Schema):
    detail: list[RecordError]
