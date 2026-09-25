from django.db import models

from .base import UUIDv7Model
from .student import Student


class StudentGroup(UUIDv7Model):
    name = models.CharField("Nombre", max_length=100, unique=True)
    students = models.ManyToManyField(
        Student,
        related_name="student_groups",
        blank=True,
        verbose_name="Estudiantes",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Grupo de estudiantes"
        verbose_name_plural = "Grupos de estudiantes"

    def __str__(self) -> str:
        return self.name
