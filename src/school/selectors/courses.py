from datetime import date

from django.db.models import Count, QuerySet

from ..models import Course, Teacher


def teacher_courses(*, teacher: Teacher) -> QuerySet[Course]:
    """Courses taught by `teacher`, optimized for detail pages."""
    return (
        Course.objects.filter(teacher=teacher)
        .select_related('subject', 'teacher', 'student_group', 'school_cycle')
        .prefetch_related('student_group__students', 'schedule_slots')
    )


def teacher_dashboard_courses(*, teacher: Teacher, value: date) -> QuerySet[Course]:
    """Courses of `teacher` whose cycle contains `value`, with student counts."""
    return (
        Course.objects.filter(
            teacher=teacher,
            school_cycle__start_date__lte=value,
            school_cycle__end_date__gte=value,
        )
        .select_related('subject', 'teacher', 'student_group', 'school_cycle')
        .annotate(student_count=Count('student_group__students'))
        .prefetch_related('schedule_slots')
    )


def teacher_other_cycle_courses(*, teacher: Teacher, value: date) -> QuerySet[Course]:
    """Courses of `teacher` whose cycle does not contain `value`, ordered."""
    return (
        Course.objects.filter(teacher=teacher)
        .exclude(
            school_cycle__start_date__lte=value,
            school_cycle__end_date__gte=value,
        )
        .select_related('subject', 'teacher', 'student_group', 'school_cycle')
        .annotate(student_count=Count('student_group__students'))
        .prefetch_related('schedule_slots')
        .order_by('school_cycle__start_date', 'subject__name')
    )
