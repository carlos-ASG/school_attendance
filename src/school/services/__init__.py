"""School-domain write services (HackSoft services).

Every mutation of school entities runs through these functions; views,
API handlers and the admin are thin interfaces over them.
"""
from .calendar import validate_session_date
from .sessions import (
    create_attendance_records,
    session_create,
    session_delete,
    session_get_or_create_today,
)

__all__ = [
    'create_attendance_records',
    'session_create',
    'session_delete',
    'session_get_or_create_today',
    'validate_session_date',
]
