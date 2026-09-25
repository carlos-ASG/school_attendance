from django.db.models import Count
from django.db.models import QuerySet
from django.utils import timezone

from school.models import Course
from school.models import SchoolCycle
from school.models import Teacher


def teacher_courses(*, teacher: Teacher) -> QuerySet[Course]:
    """Courses taught by `teacher`, optimized for detail pages."""
    return (
        Course.objects.filter(teacher=teacher)
        .select_related("subject", "teacher", "student_group", "school_cycle")
        .prefetch_related("student_group__students", "schedule_slots")
    )


def teacher_current_courses(
    *,
    teacher: Teacher,
    school_cycle: SchoolCycle | None,
) -> QuerySet[Course]:
    """Courses of `teacher` in `school_cycle`, with student counts.

    An empty queryset when there is no active cycle.
    """
    if school_cycle is None:
        return Course.objects.none()
    return (
        Course.objects.filter(teacher=teacher, school_cycle=school_cycle)
        .select_related("subject", "teacher", "student_group", "school_cycle")
        .annotate(student_count=Count("student_group__students"))
        .prefetch_related("schedule_slots")
    )


def teacher_previous_cycle_courses(
    *,
    teacher: Teacher,
    school_cycle: SchoolCycle | None,
) -> QuerySet[Course]:
    """Courses of `teacher` in cycles that ended before `school_cycle` started.

    When `school_cycle` is None the anchor falls back to today, so courses
    in already-finished cycles remain visible. Ordered oldest cycle first.
    """
    anchor = (
        school_cycle.start_date if school_cycle is not None else timezone.now().date()
    )
    return (
        Course.objects.filter(teacher=teacher, school_cycle__end_date__lt=anchor)
        .select_related("subject", "teacher", "student_group", "school_cycle")
        .annotate(student_count=Count("student_group__students"))
        .prefetch_related("schedule_slots")
        .order_by("school_cycle__start_date", "subject__name")
    )
