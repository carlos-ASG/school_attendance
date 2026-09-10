from django.conf import settings
from django.db import models
from django.db.models import Q


class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta:
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class StudentGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    students = models.ManyToManyField(Student, related_name='student_groups', blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Classroom(models.Model):
    student_group = models.ForeignKey(StudentGroup, on_delete=models.PROTECT, related_name='classrooms')
    teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT, related_name='classrooms')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='classrooms')

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=('teacher', 'subject', 'student_group'),
                name='unique_classroom_teacher_subject_group',
            )
        ]
        ordering = ('subject__name',)

    def __str__(self):
        return f'{self.subject} — {self.teacher} ({self.student_group})'


class ClassSchedule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'
        SUNDAY = 6, 'Sunday'

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='schedule_slots')
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ('classroom', 'weekday', 'start_time')
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(start_time__lt=models.F('end_time')),
                name='classschedule_start_before_end',
            )
        ]

    def __str__(self):
        return f'{self.classroom}: {self.get_weekday_display()} {self.start_time}-{self.end_time}'


class AttendanceSession(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField()
    created_by = models.ForeignKey(Teacher, on_delete=models.PROTECT, related_name='created_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('-date', '-created_at')
        constraints = [
            models.UniqueConstraint(fields=('classroom', 'date'), name='unique_session_classroom_date')
        ]

    def __str__(self):
        return f'{self.classroom} — {self.date}'


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        EXCUSED = 'EXCUSED', 'Excused'

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)

    class Meta:
        ordering = ('student__last_name', 'student__first_name')
        constraints = [
            models.UniqueConstraint(fields=('session', 'student'), name='unique_record_session_student')
        ]

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
