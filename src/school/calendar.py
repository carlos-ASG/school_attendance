"""Shared school-calendar helpers (design D5).

Pure functions that act as the single source of truth for session-date
validation and its Spanish error messages. Every session-creation entry
point (model clean, panel form, today flow, admin) calls these.
"""
from datetime import date

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from .models import NonSchoolDay, SchoolCycle

SESSION_FROZEN_MESSAGE = (
    'Esta sesión pertenece a un ciclo anterior y es de solo lectura.'
)


def get_active_cycle(value: date) -> SchoolCycle | None:
    """Return the single SchoolCycle containing the date, or None."""
    return (
        SchoolCycle.objects.filter(start_date__lte=value, end_date__gte=value)
        .order_by('pk')
        .first()
    )


def get_non_school_day(cycle: SchoolCycle | None, value: date) -> NonSchoolDay | None:
    """Return the NonSchoolDay of `cycle` covering `value`, or None."""
    if cycle is None:
        return None
    return (
        cycle.non_school_days.filter(
            (Q(end_date__isnull=True) & Q(start_date=value))
            | (Q(start_date__lte=value) & Q(end_date__gte=value))
        )
        .order_by('pk')
        .first()
    )


def session_is_frozen(session, value: date | None = None) -> bool:
    """Return True when `session` is read-only for its Teacher (design D1).

    A session is frozen when its course's School Cycle does not contain today,
    or when the course has no cycle at all. When today falls in a gap between
    cycles every session is frozen. `value` may be pre-computed by the caller
    to avoid a repeated ``timezone.now()`` call.
    """
    if value is None:
        value = timezone.now().date()
    course = session.course
    if course.school_cycle_id is None:
        return True
    return not course.school_cycle.contains_date(value)


def validate_session_date(
    course, value: date, non_school_day: NonSchoolDay | None = None
) -> None:
    """Raise ValidationError when `value` cannot host a session of `course`.

    The date must fall inside the course's cycle and must not be a
    non-school day of that cycle. `non_school_day` may be pre-computed by the
    caller (e.g. cached in the dashboard view) to avoid a repeated query.
    """
    cycle = course.school_cycle
    if cycle is None:
        raise ValidationError('El curso no tiene ciclo escolar asignado.')
    if not cycle.contains_date(value):
        raise ValidationError(
            f'La fecha está fuera del ciclo {cycle} '
            f'({cycle.start_date} al {cycle.end_date}).'
        )
    if non_school_day is None:
        non_school_day = get_non_school_day(cycle, value)
    if non_school_day is not None:
        formatted = value.strftime('%d/%m/%Y')
        raise ValidationError(f'El {formatted} es inhábil: {non_school_day.name}.')


def today_session_block_reason(
    course, value: date, non_school_day: NonSchoolDay | None = None
) -> str | None:
    """Return a readable reason why `value` cannot host a session, or None.

    Used by the teacher panel to disable the "Sesión de hoy" cards with a
    visible explanation. `non_school_day` may be pre-computed by the caller
    to avoid a repeated query per course.
    """
    try:
        validate_session_date(course, value, non_school_day)
    except ValidationError as error:
        return ' '.join(error.messages)
    return None
