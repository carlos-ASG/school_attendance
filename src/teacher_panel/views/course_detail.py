from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Count, QuerySet
from django.utils import timezone
from django.views.generic import DetailView

from school.models import AttendanceRecord, Course
from school.services import validate_session_date

from .mixins import TeacherRequiredMixin

ATTENDED_STATUSES = (
    AttendanceRecord.Status.PRESENT,
    AttendanceRecord.Status.LATE,
    AttendanceRecord.Status.EXCUSED,
)


# --- Template views (full pages) ---

class CourseDetailView(TeacherRequiredMixin, DetailView):
    template_name = 'teacher_panel/course_detail.html'
    context_object_name = 'course'

    def get_queryset(self) -> QuerySet[Course]:
        return (
            Course.objects.filter(teacher=self.teacher)
            .select_related('subject', 'teacher', 'student_group', 'school_cycle')
            .prefetch_related('student_group__students', 'schedule_slots')
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['attendance'] = self.get_attendance_summary()
        try:
            validate_session_date(course=self.object, value=timezone.now().date())
        except ValidationError as error:
            context['today_reason'] = ' '.join(error.messages)
        else:
            context['today_reason'] = None
        return context

    def get_attendance_summary(self) -> dict[int, dict[str, Any]]:
        """Return a lookup dict keyed by student pk with attendance summary.

        Counts PRESENT, LATE and EXCUSED records as attended, using the total
        number of sessions for the course as the denominator. Issues at most
        two queries regardless of the number of students.
        """
        students = self.object.student_group.students.all()
        total = self.object.sessions.count()
        if total == 0:
            return {
                student.pk: {
                    'student': student,
                    'attended': 0,
                    'total': 0,
                    'percentage': '0',
                }
                for student in students
            }
        attended_rows = (
            AttendanceRecord.objects.filter(
                session__course=self.object,
                status__in=ATTENDED_STATUSES,
            )
            .values('student_id')
            .annotate(attended=Count('pk'))
        )
        attended_by_student = {row['student_id']: row['attended'] for row in attended_rows}
        summary = {}
        for student in students:
            attended = attended_by_student.get(student.pk, 0)
            summary[student.pk] = {
                'student': student,
                'attended': attended,
                'total': total,
                'percentage': f'{attended / total * 100:.1f}',
            }
        return summary
