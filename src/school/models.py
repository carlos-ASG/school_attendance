from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


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


class Teacher(models.Model):
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


class Subject(models.Model):
    name = models.CharField('Nombre', max_length=100, unique=True)
    code = models.CharField('Código', max_length=20, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'

    def __str__(self) -> str:
        return self.name


class StudentGroup(models.Model):
    name = models.CharField('Nombre', max_length=100, unique=True)
    students = models.ManyToManyField(
        Student, related_name='student_groups', blank=True, verbose_name='Estudiantes'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Grupo de estudiantes'
        verbose_name_plural = 'Grupos de estudiantes'

    def __str__(self) -> str:
        return self.name


class Course(models.Model):
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
                fields=('teacher', 'subject', 'student_group'),
                name='unique_course_teacher_subject_group',
            )
        ]
        ordering = ('subject__name',)
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

    def __str__(self) -> str:
        return f'{self.subject} — {self.teacher} ({self.student_group})'


class ClassSchedule(models.Model):
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


class AttendanceSession(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='sessions', verbose_name='Curso'
    )
    date = models.DateField('Fecha')
    created_by = models.ForeignKey(
        Teacher, on_delete=models.PROTECT, related_name='created_sessions', verbose_name='Creado por'
    )
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField(
        'Última actualización', auto_now=True, null=True, blank=True
    )

    class Meta:
        ordering = ('-date', '-created_at')
        constraints = [
            models.UniqueConstraint(fields=('course', 'date'), name='unique_session_course_date')
        ]
        verbose_name = 'Sesión de asistencia'
        verbose_name_plural = 'Sesiones de asistencia'

    def __str__(self) -> str:
        return f'{self.course} — {self.date}'

    def clean(self) -> None:
        super().clean()
        if self.date and self.date > timezone.now().date():
            raise ValidationError({'date': 'La fecha no puede ser posterior a hoy.'})


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Presente'
        ABSENT = 'ABSENT', 'Ausente'
        LATE = 'LATE', 'Tarde'
        EXCUSED = 'EXCUSED', 'Justificado'

    session = models.ForeignKey(
        AttendanceSession, on_delete=models.CASCADE, related_name='records', verbose_name='Sesión'
    )
    student = models.ForeignKey(
        Student, on_delete=models.PROTECT, related_name='attendance_records', verbose_name='Estudiante'
    )
    status = models.CharField(
        'Estado', max_length=10, choices=Status.choices, default=Status.PRESENT
    )
    notes = models.TextField('Notas', blank=True, default='')
    updated_at = models.DateTimeField(
        'Última actualización', auto_now=True, null=True, blank=True
    )

    class Meta:
        ordering = ('student__paternal_surname', 'student__maternal_surname', 'student__first_name')
        constraints = [
            models.UniqueConstraint(fields=('session', 'student'), name='unique_record_session_student')
        ]
        verbose_name = 'Registro de asistencia'
        verbose_name_plural = 'Registros de asistencia'

    def __str__(self) -> str:
        return f'{self.student}: {self.status} ({self.session})'

    def clean(self) -> None:
        super().clean()
        if self.session_id and self.student_id:
            group = self.session.course.student_group
            if not group.students.filter(pk=self.student_id).exists():
                raise ValidationError(
                    {'student': 'El estudiante no pertenece al grupo del curso de la sesión.'}
                )


def create_attendance_records(session: AttendanceSession) -> int:
    """Create one AttendanceRecord per student in the session's course group.

    Skips students that already have a record in the session. Returns the number
    of records created.
    """
    students = session.course.student_group.students.all()
    existing = set(
        AttendanceRecord.objects.filter(session=session, student__in=students).values_list(
            'student_id', flat=True
        )
    )
    to_create = [AttendanceRecord(session=session, student=s) for s in students if s.id not in existing]
    AttendanceRecord.objects.bulk_create(to_create)
    return len(to_create)
