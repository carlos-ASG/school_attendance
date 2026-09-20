from django.db import models

from ..images import ConvertedPhotoStorage
from .base import UUIDv7Model


class Student(UUIDv7Model):
    first_name = models.CharField('Nombre', max_length=100)
    paternal_surname = models.CharField('Apellido paterno', max_length=100)
    maternal_surname = models.CharField('Apellido materno', max_length=100)
    email = models.EmailField('Correo electrónico', blank=True, null=True)
    photo = models.ImageField(
        'Fotografía',
        blank=True,
        upload_to='students/',
        storage=ConvertedPhotoStorage(),
    )

    def save(self, *args, **kwargs):
        previous_photo = None
        if not self._state.adding and self.pk is not None:
            previous_photo = (
                Student.objects.filter(pk=self.pk).values_list('photo', flat=True).first()
            )
        super().save(*args, **kwargs)
        if previous_photo and previous_photo != self.photo.name:
            storage = self.photo.storage
            if storage.exists(previous_photo):
                storage.delete(previous_photo)

    class Meta:
        ordering = ('paternal_surname', 'maternal_surname', 'first_name')
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

    def __str__(self) -> str:
        surnames = f'{self.paternal_surname} {self.maternal_surname}'.strip()
        return f'{surnames}, {self.first_name}'
