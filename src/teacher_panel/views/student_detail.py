from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from school.models import AttendanceRecord, Course, Student

from .course_detail import ATTENDED_STATUSES
from .mixins import TeacherRequiredMixin


class StudentDetailView(TeacherRequiredMixin, DetailView):
    """Course-scoped student detail: photo, personal data and attendance (D1-D3)."""

    template_name = 'teacher_panel/student_detail.html'
    context_object_name = 'student'

    def get_queryset(self) -> QuerySet[Student]:
        self.course = get_object_or_404(
            Course.objects.select_related(
                'subject', 'teacher', 'student_group', 'school_cycle'
            ),
            pk=self.kwargs['course_pk'],
            teacher=self.teacher,
        )
        return Student.objects.filter(student_groups=self.course.student_group)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        context['attendance'] = self.get_attendance_summary()
        return context

    def get_attendance_summary(self) -> dict[str, Any]:
        """Reuse the course detail formula: attended / total sessions (D3)."""
        total = self.course.sessions.count()
        if total == 0:
            return {'attended': 0, 'total': 0, 'percentage': '0'}
        attended = AttendanceRecord.objects.filter(
            session__course=self.course,
            student=self.object,
            status__in=ATTENDED_STATUSES,
        ).count()
        return {
            'attended': attended,
            'total': total,
            'percentage': f'{attended / total * 100:.1f}',
        }
