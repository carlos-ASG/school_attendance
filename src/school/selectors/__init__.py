"""Read-only school-domain queries (HackSoft selectors).

Selectors are the single source of truth for fetching school entities in
the teacher panel, API and services. They never mutate data.
"""
from .attendance import (
    get_course_attendance_summary,
    get_student_attendance_summary,
)
from .calendar import get_current_school_cycle, get_non_school_day
from .courses import (
    teacher_courses,
    teacher_current_courses,
    teacher_previous_cycle_courses,
)
from .sessions import (
    course_history_sessions,
    get_today_session,
    teacher_sessions,
)
from .students import course_students, get_student
from .teachers import get_teacher

__all__ = [
    'course_history_sessions',
    'course_students',
    'get_course_attendance_summary',
    'get_current_school_cycle',
    'get_non_school_day',
    'get_student',
    'get_student_attendance_summary',
    'get_teacher',
    'get_today_session',
    'teacher_courses',
    'teacher_current_courses',
    'teacher_previous_cycle_courses',
    'teacher_sessions',
]
