"""School-calendar domain services (design D5).

`validate_session_date` is the single source of truth for session-date
validation and its Spanish error messages. Every session-creation entry
point (model clean, panel form, today flow, admin) calls it. A session
date is valid only when it falls inside the course's cycle, is not a
non-school day, and falls on a weekday the course's ClassSchedule slots
cover (a course without slots has no valid session dates).
"""
from datetime import date

from django.core.exceptions import ValidationError

from ..models import ClassSchedule, Course, NonSchoolDay, SchoolCycle
from ..selectors import get_non_school_day


def validate_session_date(
    *,
    course: Course,
    value: date,
    non_school_day: NonSchoolDay | None = None,
) -> None:
    """Raise ValidationError when `value` cannot host a session of `course`.

    Three rules apply, in order:

    1. The date must fall inside the course's cycle.
    2. The date must not be a non-school day of that cycle.
    3. The course must have ClassSchedule slots and one of them must match
       the date's weekday. Slot start/end times are ignored: only the
       weekday matters. A course without slots can never host a session.

    `non_school_day` may be pre-computed by the caller (e.g. cached in the
    dashboard view) to avoid a repeated query. The schedule check uses the
    course's related manager, which reuses the prefetch cache when the
    caller prefetched ``schedule_slots``.
    """
    cycle: SchoolCycle | None = course.school_cycle
    if cycle is None:
        raise ValidationError('El curso no tiene ciclo escolar asignado.')
    if not cycle.contains_date(value):
        raise ValidationError(
            f'La fecha está fuera del ciclo {cycle} '
            f'({cycle.start_date} al {cycle.end_date}).'
        )
    if non_school_day is None:
        non_school_day = get_non_school_day(cycle=cycle, value=value)
    if non_school_day is not None:
        formatted = value.strftime('%d/%m/%Y')
        raise ValidationError(f'El {formatted} es inhábil: {non_school_day.name}.')
    scheduled_weekdays = {slot.weekday for slot in course.schedule_slots.all()}
    if not scheduled_weekdays:
        raise ValidationError('El curso no tiene horario asignado.')
    if value.weekday() not in scheduled_weekdays:
        weekday = ClassSchedule.Weekday(value.weekday()).label.lower()
        raise ValidationError(f'El curso no tiene clase los días {weekday}.')
