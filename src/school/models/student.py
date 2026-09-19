from django.db import models


class Student(models.Model):
    first_name = models.CharField('Nombre', max_length=100)
    paternal_surname = models.CharField('Apellido paterno', max_length=100)
    maternal_surname = models.CharField('Apellido materno', max_length=100)
    email = models.EmailField('Correo electrónico', blank=True, null=True)

    class Meta:
        ordering = ('paternal_surname', 'maternal_surname', 'first_name')
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

    def __str__(self) -> str:
        surnames = f'{self.paternal_surname} {self.maternal_surname}'.strip()
        return f'{surnames}, {self.first_name}'
