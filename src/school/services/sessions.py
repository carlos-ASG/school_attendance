"""Attendance-session write services."""
from datetime import date

from django.db import transaction
from django.utils import timezone

from ..models import AttendanceRecord, AttendanceSession, Course, Teacher
from ..selectors import get_today_session
from .calendar import validate_session_date


def create_attendance_records(session: AttendanceSession) -> int:
    """Create one AttendanceRecord per student in the session's course group.

    Skips students that already have a record in the session. Returns the number
    of records created.
    """
    students = session.course.student_group.students.all()
    existing = set(
        AttendanceRecord.objects.filter(session=session, student__in=students).values_list(
            'student_id', flat=True
        )
    )
    to_create = [AttendanceRecord(session=session, student=s) for s in students if s.id not in existing]
    AttendanceRecord.objects.bulk_create(to_create)
    return len(to_create)


def session_create(
    *, course: Course, value: date, created_by: Teacher
) -> AttendanceSession:
    """Create a session for `course` on `value` with one record per student."""
    with transaction.atomic():
        session = AttendanceSession.objects.create(
            course=course, date=value, created_by=created_by
        )
        create_attendance_records(session)
    return session


def session_get_or_create_today(
    *, course: Course, created_by: Teacher, value: date | None = None
) -> tuple[AttendanceSession, bool]:
    """Return (session, created) for the course's session on `value` (today).

    An existing session is returned as-is, without re-validation. Creating
    runs the calendar validation first: out-of-cycle, non-school-day and
    non-scheduled weekday dates raise ValidationError and persist nothing.
    """
    if value is None:
        value = timezone.now().date()
    session = get_today_session(course=course, value=value)
    if session is not None:
        return session, False
    validate_session_date(course=course, value=value)
    session = session_create(course=course, value=value, created_by=created_by)
    return session, True


def session_delete(*, session: AttendanceSession) -> None:
    """Delete the session and its records; callers guard frozen sessions."""
    with transaction.atomic():
        session.delete()
