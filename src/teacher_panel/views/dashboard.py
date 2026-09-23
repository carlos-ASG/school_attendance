from typing import Any

from django.db.models import QuerySet
from django.utils import timezone
from django.views.generic import ListView

from school.models import Course
from school.selectors import (
    get_active_cycle,
    get_non_school_day,
    teacher_dashboard_courses,
    teacher_other_cycle_courses,
)

from .mixins import TeacherRequiredMixin

# --- Template views (full pages) ---

class DashboardView(TeacherRequiredMixin, ListView):
    template_name = 'teacher_panel/dashboard.html'
    context_object_name = 'courses'

    def get_queryset(self) -> QuerySet[Course]:
        return teacher_dashboard_courses(
            teacher=self.teacher, value=timezone.now().date()
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

        context['other_cycle_courses'] = teacher_other_cycle_courses(
            teacher=self.teacher, value=today
        )
        return context
