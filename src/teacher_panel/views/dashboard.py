from typing import Any

from django.db.models import Count, QuerySet
from django.utils import timezone
from django.views.generic import ListView

from school.models import Course
from school.selectors import get_active_cycle, get_non_school_day

from .mixins import TeacherRequiredMixin

# --- Template views (full pages) ---

class DashboardView(TeacherRequiredMixin, ListView):
    template_name = 'teacher_panel/dashboard.html'
    context_object_name = 'courses'

    def get_queryset(self) -> QuerySet[Course]:
        today = timezone.now().date()
        return (
            Course.objects.filter(
                teacher=self.teacher,
                school_cycle__start_date__lte=today,
                school_cycle__end_date__gte=today,
            )
            .select_related('subject', 'teacher', 'student_group', 'school_cycle')
            .annotate(student_count=Count('student_group__students'))
            .prefetch_related('schedule_slots')
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        active_cycle = get_active_cycle(value=today)
        non_school_day = (
            get_non_school_day(cycle=active_cycle, value=today)
            if active_cycle
            else None
        )
        context['active_cycle'] = active_cycle
        context['non_school_day'] = non_school_day

        context['other_cycle_courses'] = (
            Course.objects.filter(teacher=self.teacher)
            .exclude(
                school_cycle__start_date__lte=today,
                school_cycle__end_date__gte=today,
            )
            .select_related('subject', 'teacher', 'student_group', 'school_cycle')
            .annotate(student_count=Count('student_group__students'))
            .prefetch_related('schedule_slots')
            .order_by('school_cycle__start_date', 'subject__name')
        )
        return context
