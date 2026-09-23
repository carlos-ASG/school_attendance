from typing import Any

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView

from school.models import AttendanceSession
from school.selectors import teacher_courses, teacher_sessions
from school.services import session_get_or_create_today

from .mixins import TeacherRequiredMixin


def serialize_records(session: AttendanceSession) -> list[dict[str, Any]]:
    """Serialize a session's records for the Alpine attendance panel."""
    return [
        {
            'id': record.pk,
            'student': str(record.student),
            'status': record.status,
            'notes': record.notes,
        }
        for record in session.records.select_related('student')
    ]


class TodaySessionCreateView(TeacherRequiredMixin, View):
    """POST-only: get-or-create today's session for a course, then redirect (D4)."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        course = get_object_or_404(
            teacher_courses(teacher=self.teacher), pk=kwargs['pk']
        )
        try:
            session, created = session_get_or_create_today(
                course=course, created_by=self.teacher
            )
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
            return HttpResponseRedirect(
                reverse('teacher_panel:course_detail', args=[course.pk])
            )
        if created:
            messages.success(request, 'Sesión creada.')
        return HttpResponseRedirect(
            reverse('teacher_panel:today_session_detail', args=[session.pk])
        )


class TodaySessionDetailView(TeacherRequiredMixin, DetailView):
    template_name = 'teacher_panel/today_session_detail.html'
    context_object_name = 'session'

    def get_queryset(self) -> QuerySet[AttendanceSession]:
        return teacher_sessions(teacher=self.teacher)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        if self.object.date != timezone.now().date():
            return HttpResponseRedirect(
                reverse('teacher_panel:session_detail', args=[self.object.pk])
            )
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['records'] = serialize_records(self.object)
        context['save_url'] = reverse(
            'api:update_session_records', args=[self.object.pk]
        )
        return context
