from typing import Any

from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.generic import View

from school.models import Course
from school.selectors import get_course_attendance_summary
from school.selectors import teacher_courses
from teacher_panel.forms import AttendanceSummaryFilterForm

from .mixins import TeacherRequiredMixin

# --- Template views (full pages + HTMX fragment) ---


class CourseAttendanceSummaryView(TeacherRequiredMixin, View):
    """Per-student attendance summary scoped by an optional date range (D1-D5).

    Same URL serves the full page and the `attendance_summary` fragment: an
    HTMX filter submission re-renders only the fragment, a direct GET renders
    the whole page with the same bounds applied.
    """

    template_name = "teacher_panel/course_attendance_summary.html"

    def get_course(self) -> Course:
        return get_object_or_404(
            teacher_courses(teacher=self.teacher),
            pk=self.kwargs["pk"],
        )

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        course = self.get_course()
        form = AttendanceSummaryFilterForm(request.GET)
        context = {
            "course": course,
            "form": form,
            "attendance": {},
        }
        if form.is_valid():
            context["attendance"] = get_course_attendance_summary(
                course=course,
                date_from=form.cleaned_data["date_from"],
                date_to=form.cleaned_data["date_to"],
            )
            context["has_sessions"] = any(
                row["total"] > 0 for row in context["attendance"].values()
            )
        if request.htmx:  # type: ignore[attr-defined]
            return render(
                request,
                f"{self.template_name}#attendance_summary",
                context,
            )
        return render(request, self.template_name, context)
