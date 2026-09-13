from django.db.models import Count
from django.views.generic import ListView

from school.models import Course

from .mixins import TeacherRequiredMixin

# --- Template views (full pages) ---

class DashboardView(TeacherRequiredMixin, ListView):
    template_name = 'teachers/dashboard.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return (
            Course.objects.filter(teacher=self.teacher)
            .select_related('subject', 'teacher', 'student_group')
            .annotate(student_count=Count('student_group__students'))
        )
