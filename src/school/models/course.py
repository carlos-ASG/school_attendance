from django.db import models

from .school_cycle import SchoolCycle
from .student_group import StudentGroup
from .subject import Subject
from .teacher import Teacher


class Course(models.Model):
    school_cycle = models.ForeignKey(
        SchoolCycle,
        on_delete=models.PROTECT,
        related_name='courses',
        verbose_name='Ciclo escolar',
    )
    student_group = models.ForeignKey(
        StudentGroup, on_delete=models.PROTECT, related_name='courses', verbose_name='Grupo de estudiantes'
    )
    teacher = models.ForeignKey(
        Teacher, on_delete=models.PROTECT, related_name='courses', verbose_name='Profesor'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name='courses', verbose_name='Materia'
    )
    classroom = models.CharField('Aula', max_length=50, blank=True, default='')
    updated_at = models.DateTimeField(
        'Última actualización', auto_now=True, null=True, blank=True
    )

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=('teacher', 'subject', 'student_group', 'school_cycle'),
                name='unique_course_teacher_subject_group_school_cycle',
            ),
        ]
        ordering = ('subject__name',)
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

    def __str__(self) -> str:
        return f'{self.subject} — {self.teacher} ({self.student_group})'
