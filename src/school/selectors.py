"""Read-only school-calendar queries.

Selectors are the single source of truth for fetching the calendar
entities (SchoolCycle, NonSchoolDay) that session-date validation and the
teacher panel depend on. They never mutate data.
"""
from datetime import date
from uuid import UUID

from django.db.models import Q

from .models import NonSchoolDay, SchoolCycle, Student


def get_active_cycle(*, value: date) -> SchoolCycle | None:
    """Return the single SchoolCycle containing the date, or None."""
    return (
        SchoolCycle.objects.filter(start_date__lte=value, end_date__gte=value)
        .order_by('pk')
        .first()
    )


def get_student(*, student_id: UUID) -> Student | None:
    """Return the Student with pk=student_id, or None."""
    return Student.objects.filter(pk=student_id).first()


def get_non_school_day(
    *, cycle: SchoolCycle | None, value: date
) -> NonSchoolDay | None:
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
