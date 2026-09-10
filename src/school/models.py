from django.conf import settings
from django.db import models
from django.db.models import Q


class Student(models.Model):
    first_name = models.CharField('Nombre', max_length=100)
    paternal_surname = models.CharField('Apellido paterno', max_length=100)
    maternal_surname = models.CharField('Apellido materno', max_length=100)
    email = models.EmailField('Correo electrónico', blank=True, null=True)

    class Meta:
        ordering = ('paternal_surname', 'maternal_surname', 'first_name')
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

    def __str__(self):
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

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Subject(models.Model):
    name = models.CharField('Nombre', max_length=100, unique=True)
    code = models.CharField('Código', max_length=20, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'

    def __str__(self):
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

    def __str__(self):
        return self.name


class Classroom(models.Model):
    student_group = models.ForeignKey(
        StudentGroup, on_delete=models.PROTECT, related_name='classrooms', verbose_name='Grupo de estudiantes'
    )
    teacher = models.ForeignKey(
        Teacher, on_delete=models.PROTECT, related_name='classrooms', verbose_name='Profesor'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name='classrooms', verbose_name='Materia'
    )

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=('teacher', 'subject', 'student_group'),
                name='unique_classroom_teacher_subject_group',
            )
        ]
        ordering = ('subject__name',)
        verbose_name = 'Aula'
        verbose_name_plural = 'Aulas'

    def __str__(self):
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

    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, related_name='schedule_slots', verbose_name='Aula'
    )
    weekday = models.IntegerField('Día de la semana', choices=Weekday.choices)
    start_time = models.TimeField('Hora de inicio')
    end_time = models.TimeField('Hora de fin')

    class Meta:
        ordering = ('classroom', 'weekday', 'start_time')
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(start_time__lt=models.F('end_time')),
                name='classschedule_start_before_end',
            )
        ]
        verbose_name = 'Horario de clase'
        verbose_name_plural = 'Horarios de clase'

    def __str__(self):
        return f'{self.classroom}: {self.get_weekday_display()} {self.start_time}-{self.end_time}'


class AttendanceSession(models.Model):
    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, related_name='sessions', verbose_name='Aula'
    )
    date = models.DateField('Fecha')
    created_by = models.ForeignKey(
        Teacher, on_delete=models.PROTECT, related_name='created_sessions', verbose_name='Creado por'
    )
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    notes = models.TextField('Notas', blank=True)

    class Meta:
        ordering = ('-date', '-created_at')
        constraints = [
            models.UniqueConstraint(fields=('classroom', 'date'), name='unique_session_classroom_date')
        ]
        verbose_name = 'Sesión de asistencia'
        verbose_name_plural = 'Sesiones de asistencia'

    def __str__(self):
        return f'{self.classroom} — {self.date}'


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

    class Meta:
        ordering = ('student__paternal_surname', 'student__maternal_surname', 'student__first_name')
        constraints = [
            models.UniqueConstraint(fields=('session', 'student'), name='unique_record_session_student')
        ]
        verbose_name = 'Registro de asistencia'
        verbose_name_plural = 'Registros de asistencia'

    def __str__(self):
        return f'{self.student}: {self.status} ({self.session})'


def create_attendance_records(session: AttendanceSession) -> int:
    """Create one AttendanceRecord per student in the session's classroom group.

    Skips students that already have a record in the session. Returns the number
    of records created.
    """
    students = session.classroom.student_group.students.all()
    existing = set(
        AttendanceRecord.objects.filter(session=session, student__in=students).values_list(
            'student_id', flat=True
        )
    )
    to_create = [AttendanceRecord(session=session, student=s) for s in students if s.id not in existing]
    AttendanceRecord.objects.bulk_create(to_create)
    return len(to_create)
