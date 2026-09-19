from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from .school_cycle import SchoolCycle


class NonSchoolDay(models.Model):
    class DayType(models.TextChoices):
        ASUETO = 'ASUETO', 'Asueto'
        VACACIONES = 'VACACIONES', 'Vacaciones'
        OTRO = 'OTRO', 'Otro'

    cycle = models.ForeignKey(
        SchoolCycle,
        on_delete=models.CASCADE,
        related_name='non_school_days',
        verbose_name='Ciclo escolar',
    )
    name = models.CharField('Nombre', max_length=100)
    day_type = models.CharField('Tipo', max_length=10, choices=DayType.choices)
    start_date = models.DateField('Fecha de inicio')
    end_date = models.DateField('Fecha de fin', null=True, blank=True)

    class Meta:
        ordering = ('start_date',)
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(end_date__gte=F('start_date')),
                name='nonschoolday_end_after_start',
            )
        ]
        verbose_name = 'Día inhábil'
        verbose_name_plural = 'Días inhábiles'

    def __str__(self) -> str:
        if self.end_date is None:
            return self.name
        return f'{self.name} ({self.start_date} – {self.end_date})'

    def contains_date(self, value: date) -> bool:
        if self.end_date is None:
            return value == self.start_date
        return self.start_date <= value <= self.end_date

    def clean(self) -> None:
        super().clean()
        errors: dict[str, ValidationError] = {}
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors['end_date'] = ValidationError(
                'La fecha de fin debe ser igual o posterior a la fecha de inicio.'
            )
        if self.cycle_id and self.cycle.start_date and self.cycle.end_date:
            outside = (
                (self.start_date is not None and not self.cycle.contains_date(self.start_date))
                or (self.end_date is not None and not self.cycle.contains_date(self.end_date))
            )
            if outside:
                errors['start_date'] = ValidationError(
                    f'Las fechas deben estar dentro del ciclo «{self.cycle}» '
                    f'({self.cycle.start_date} al {self.cycle.end_date}).'
                )
        if errors:
            raise ValidationError(errors)
