from django.db import models
from django.db.models import Q
from uuid6 import uuid7

from school.models import Student

from .credential import Credential


class StudentCredential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='credential_links',
        verbose_name='Estudiante',
    )
    credential = models.OneToOneField(
        Credential,
        on_delete=models.CASCADE,
        related_name='student_link',
        verbose_name='Credencial',
    )
    linked_at = models.DateTimeField('Fecha de vinculación', null=True, blank=True)
    unlinked_at = models.DateTimeField('Fecha de desvinculación', null=True, blank=True)

    class Meta:
        ordering = ('-linked_at',)
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=['student'],
                condition=Q(unlinked_at__isnull=True),
                name='studentcredential_one_active_per_student',
            )
        ]
        verbose_name = 'Relación estudiante-credencial'
        verbose_name_plural = 'Relaciones estudiante-credencial'

    def __str__(self) -> str:
        return f'{self.student} ↔ {self.credential}'
