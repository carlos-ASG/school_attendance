from django.db import models

from .base import UUIDv7Model


class Subject(UUIDv7Model):
    name = models.CharField("Nombre", max_length=100, unique=True)
    code = models.CharField("Código", max_length=20, blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Materia"
        verbose_name_plural = "Materias"

    def __str__(self) -> str:
        return self.name
