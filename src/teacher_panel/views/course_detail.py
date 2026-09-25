from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils import timezone
from django.views.generic import DetailView

from school.models import Course
from school.selectors import get_course_attendance_summary
from school.selectors import teacher_courses
from school.services import validate_session_date

from .mixins import TeacherRequiredMixin

# --- Template views (full pages) ---


class CourseDetailView(TeacherRequiredMixin, DetailView):
    template_name = "teacher_panel/course_detail.html"
    context_object_name = "course"

    def get_queryset(self) -> QuerySet[Course]:
        return teacher_courses(teacher=self.teacher)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["attendance"] = get_course_attendance_summary(course=self.object)
        try:
            validate_session_date(course=self.object, value=timezone.now().date())
        except ValidationError as error:
            context["today_reason"] = " ".join(error.messages)
        else:
            context["today_reason"] = None
        return context
