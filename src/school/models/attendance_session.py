from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .base import UUIDv7Model
from .course import Course
from .teacher import Teacher


class AttendanceSession(UUIDv7Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='sessions', verbose_name='Curso'
    )
    date = models.DateField('Fecha')
    created_by = models.ForeignKey(
        Teacher, on_delete=models.PROTECT, related_name='created_sessions', verbose_name='Creado por'
    )
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField(
        'Última actualización', auto_now=True, null=True, blank=True
    )

    class Meta:
        ordering = ('-date', '-created_at')
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(fields=('course', 'date'), name='unique_session_course_date')
        ]
        verbose_name = 'Sesión de asistencia'
        verbose_name_plural = 'Sesiones de asistencia'

    def __str__(self) -> str:
        return f'{self.course} — {self.date}'

    def clean(self) -> None:
        """Validate the session date before saving.

        Two rules apply, in order:

        1. The date must not be in the future (mirrors the rule enforced in
           ``SessionForm``).
        2. Calendar validation (creation-time only, design D6): for a new
           session (``_state.adding`` is ``True``) the date must fall inside
           the course's school cycle, must not be a non-school day, and must
           fall on a weekday the course's ClassSchedule slots cover (a
           course without slots can never host a session).
           Existing sessions are never invalidated or blocked from editing
           when the calendar or schedule changes afterwards — sessions are
           historical truth. Errors are attached to the ``date`` field and
           name the offending cycle, non-school day, or weekday in Spanish.

        Raises:
            ValidationError: with the errors keyed by field (``date``).

        Note:
            The import of ``validate_session_date`` is deferred to call time to
            avoid a circular import (``calendar`` imports this models package).
        """
        super().clean()
        if self.date and self.date > timezone.now().date():
            raise ValidationError({'date': 'La fecha no puede ser posterior a hoy.'})
        if self._state.adding and self.course_id and self.date:
            # Creation-time-only validation (design D6): existing sessions
            # are never invalidated or blocked by later calendar changes.
            # _state.adding (not pk is None) because the UUID v7 default
            # assigns a pk at __init__ for every new instance.
            from ..calendar import validate_session_date

            try:
                validate_session_date(self.course, self.date)
            except ValidationError as error:
                raise ValidationError({'date': error.messages}) from error
