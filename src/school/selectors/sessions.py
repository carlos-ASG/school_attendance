from datetime import date

from django.db.models import QuerySet

from ..models import AttendanceSession, Course, Teacher


def teacher_sessions(*, teacher: Teacher) -> QuerySet[AttendanceSession]:
    """Sessions of the teacher's courses, optimized for detail pages."""
    return AttendanceSession.objects.filter(
        course__teacher=teacher
    ).select_related(
        'course__subject',
        'course__student_group',
        'course__school_cycle',
        'created_by',
    )


def course_history_sessions(
    *, course: Course, value: date
) -> QuerySet[AttendanceSession]:
    """The course's sessions on dates other than `value` (history list)."""
    return course.sessions.exclude(date=value)


def get_today_session(
    *, course: Course, value: date
) -> AttendanceSession | None:
    """Return the course's session on `value`, or None."""
    return course.sessions.filter(date=value).first()
