from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

# Duration bounds per cycle type, in days (see design D4). The ranges are
# intentionally generous and overlapping: the type guards against absurd
# durations, it does not strictly classify.
ANNUAL_DURATION_DAYS = (240, 400)
SEMESTRAL_DURATION_DAYS = (110, 240)
QUATRIMESTRAL_DURATION_DAYS = (85, 145)

DURATION_BOUNDS_BY_TYPE: dict[str, tuple[int, int]] = {
    'ANNUAL': ANNUAL_DURATION_DAYS,
    'SEMESTRAL': SEMESTRAL_DURATION_DAYS,
    'QUATRIMESTRAL': QUATRIMESTRAL_DURATION_DAYS,
}


def cycle_duration_days(start_date: date, end_date: date) -> int:
    """Return the cycle duration in days (end minus start)."""
    return (end_date - start_date).days


class SchoolCycle(models.Model):
    class CycleType(models.TextChoices):
        ANNUAL = 'ANNUAL', 'Anual'
        SEMESTRAL = 'SEMESTRAL', 'Semestral'
        QUATRIMESTRAL = 'QUATRIMESTRAL', 'Cuatrimestral'

    name = models.CharField('Nombre', max_length=100)
    cycle_type = models.CharField(
        'Tipo de ciclo', max_length=15, choices=CycleType.choices
    )
    start_date = models.DateField('Fecha de inicio')
    end_date = models.DateField('Fecha de fin')

    class Meta:
        ordering = ('-start_date',)
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(start_date__lt=F('end_date')),
                name='schoolcycle_start_before_end',
            )
        ]
        verbose_name = 'Ciclo escolar'
        verbose_name_plural = 'Ciclos escolares'

    def __str__(self) -> str:
        return self.name

    def contains_date(self, value: date) -> bool:
        return self.start_date <= value <= self.end_date

    def clean(self) -> None:
        super().clean()
        errors: dict[str, ValidationError] = {}
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                errors['start_date'] = ValidationError(
                    'La fecha de inicio debe ser anterior a la fecha de fin.'
                )
            else:
                bounds = DURATION_BOUNDS_BY_TYPE.get(self.cycle_type)
                if bounds is not None:
                    duration = cycle_duration_days(self.start_date, self.end_date)
                    minimum, maximum = bounds
                    if not minimum <= duration <= maximum:
                        errors['end_date'] = ValidationError(
                            f'La duración de un ciclo {self.get_cycle_type_display().lower()} '
                            f'debe estar entre {minimum} y {maximum} días '
                            f'(configurado: {duration} días).'
                        )
                overlap = self.overlapping_cycle()
                if overlap is not None:
                    errors['__all__'] = ValidationError(
                        f'Las fechas se traslapan con el ciclo «{overlap}».'
                    )
        if errors:
            raise ValidationError(errors)

    def overlapping_cycle(self) -> 'SchoolCycle | None':
        queryset = SchoolCycle.objects.filter(
            start_date__lte=self.end_date, end_date__gte=self.start_date
        )
        if self.pk is not None:
            queryset = queryset.exclude(pk=self.pk)
        return queryset.first()
