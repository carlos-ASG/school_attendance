from django.core.exceptions import ValidationError
from django.db import models

from .attendance_session import AttendanceSession
from .base import UUIDv7Model
from .student import Student


class AttendanceRecord(UUIDv7Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Presente"
        ABSENT = "ABSENT", "Ausente"
        LATE = "LATE", "Tarde"
        EXCUSED = "EXCUSED", "Justificado"

    ATTENDED_STATUSES = (Status.PRESENT, Status.LATE, Status.EXCUSED)

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="records",
        verbose_name="Sesión",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="attendance_records",
        verbose_name="Estudiante",
    )
    status = models.CharField(
        "Estado",
        max_length=10,
        choices=Status.choices,
        default=Status.PRESENT,
    )
    notes = models.TextField("Notas", blank=True, default="")
    updated_at = models.DateTimeField(
        "Última actualización",
        auto_now=True,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = (
            "student__paternal_surname",
            "student__maternal_surname",
            "student__first_name",
        )
        constraints = [
            models.UniqueConstraint(
                fields=("session", "student"), name="unique_record_session_student"
            ),
        ]
        verbose_name = "Registro de asistencia"
        verbose_name_plural = "Registros de asistencia"

    def __str__(self) -> str:
        return f"{self.student}: {self.status} ({self.session})"

    def clean(self) -> None:
        super().clean()
        if self.session_id and self.student_id:
            group = self.session.course.student_group
            if not group.students.filter(pk=self.student_id).exists():
                raise ValidationError(
                    {
                        "student": (
                            "El estudiante no pertenece al grupo del curso "
                            "de la sesión."
                        )
                    },
                )
