from django.db import models
from django.db.models import Q

from .base import UUIDv7Model
from .course import Course


class ClassSchedule(UUIDv7Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Lunes'
        TUESDAY = 1, 'Martes'
        WEDNESDAY = 2, 'Miércoles'
        THURSDAY = 3, 'Jueves'
        FRIDAY = 4, 'Viernes'
        SATURDAY = 5, 'Sábado'
        SUNDAY = 6, 'Domingo'

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='schedule_slots', verbose_name='Curso'
    )
    weekday = models.IntegerField('Día de la semana', choices=Weekday.choices)
    start_time = models.TimeField('Hora de inicio')
    end_time = models.TimeField('Hora de fin')

    class Meta:
        ordering = ('course', 'weekday', 'start_time')
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(start_time__lt=models.F('end_time')),
                name='classschedule_start_before_end',
            )
        ]
        verbose_name = 'Horario de clase'
        verbose_name_plural = 'Horarios de clase'

    def __str__(self) -> str:
        return f'{self.course}: {self.get_weekday_display()} {self.start_time}-{self.end_time}'
