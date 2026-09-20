from django.conf import settings
from django.db import models

from .base import UUIDv7Model


class Teacher(UUIDv7Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher',
        verbose_name='Usuario',
    )
    first_name = models.CharField('Nombre', max_length=100)
    last_name = models.CharField('Apellido', max_length=100)

    class Meta:
        ordering = ('last_name', 'first_name')
        verbose_name = 'Profesor'
        verbose_name_plural = 'Profesores'

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name}'
