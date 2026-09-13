from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from school.models import Course

from .mixins import TeacherRequiredMixin

# --- Template views (full pages) ---

class CourseSessionHistoryView(TeacherRequiredMixin, ListView):
    template_name = 'teachers/course_session_history.html'
    context_object_name = 'sessions'

    def get_course(self):
        return get_object_or_404(
            Course.objects.filter(teacher=self.teacher), pk=self.kwargs['pk']
        )

    def get(self, request, *args, **kwargs):
        self.course = self.get_course()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.course.sessions.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context
