from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import ListView

from school.models import Course
from school.selectors import get_current_school_cycle
from school.selectors import get_non_school_day
from school.selectors import teacher_current_courses
from school.selectors import teacher_previous_cycle_courses

from .mixins import TeacherRequiredMixin

# --- Template views (full pages) ---


class DashboardView(TeacherRequiredMixin, ListView):
    template_name = "teacher_panel/dashboard.html"
    context_object_name = "courses"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.current_cycle = get_current_school_cycle()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Course]:
        return teacher_current_courses(
            teacher=self.teacher,
            school_cycle=self.current_cycle,
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context["current_cycle"] = self.current_cycle
        context["non_school_day"] = (
            get_non_school_day(cycle=self.current_cycle, value=today)
            if self.current_cycle
            else None
        )

        context["previous_cycle_courses"] = teacher_previous_cycle_courses(
            teacher=self.teacher,
            school_cycle=self.current_cycle,
        )
        return context
