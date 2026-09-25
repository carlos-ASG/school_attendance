from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from school.models import Student
from school.selectors import course_students
from school.selectors import get_student_attendance_summary
from school.selectors import teacher_courses

from .mixins import TeacherRequiredMixin


class StudentDetailView(TeacherRequiredMixin, DetailView):
    """Course-scoped student detail: photo, personal data and attendance (D1-D3)."""

    template_name = "teacher_panel/student_detail.html"
    context_object_name = "student"

    def get_queryset(self) -> QuerySet[Student]:
        self.course = get_object_or_404(
            teacher_courses(teacher=self.teacher),
            pk=self.kwargs["course_pk"],
        )
        return course_students(course=self.course)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["course"] = self.course
        context["attendance"] = get_student_attendance_summary(
            course=self.course,
            student=self.object,
        )
        return context
