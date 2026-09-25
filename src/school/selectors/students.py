from uuid import UUID

from django.db.models import QuerySet

from school.models import Course
from school.models import Student


def get_student(*, student_id: UUID) -> Student | None:
    """Return the Student with pk=student_id, or None."""
    return Student.objects.filter(pk=student_id).first()


def course_students(*, course: Course) -> QuerySet[Student]:
    """Return the students of the course's group."""
    return Student.objects.filter(student_groups=course.student_group)
