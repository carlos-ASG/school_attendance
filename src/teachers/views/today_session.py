from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView
from django_htmx.http import retarget

from school.models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    create_attendance_records,
)

from ..forms import AttendanceFormSet
from .mixins import TeacherRequiredMixin

STATUS_CYCLE = {
    AttendanceRecord.Status.PRESENT: AttendanceRecord.Status.ABSENT,
    AttendanceRecord.Status.ABSENT: AttendanceRecord.Status.LATE,
    AttendanceRecord.Status.LATE: AttendanceRecord.Status.EXCUSED,
    AttendanceRecord.Status.EXCUSED: AttendanceRecord.Status.PRESENT,
}


# --- Template views (full pages) ---

class TodaySessionCreateView(TeacherRequiredMixin, View):
    """POST-only: get-or-create today's session for a course, then redirect (D4)."""

    def post(self, request, *args, **kwargs):
        course = get_object_or_404(
            Course.objects.filter(teacher=self.teacher), pk=kwargs['pk']
        )
        today = timezone.now().date()
        session = course.sessions.filter(date=today).first()
        if session is None:
            session = AttendanceSession.objects.create(
                course=course,
                date=today,
                created_by=self.teacher,
            )
            create_attendance_records(session)
            messages.success(request, 'Sesión creada.')
        return HttpResponseRedirect(
            reverse('teachers:today_session_detail', args=[session.pk])
        )


class TodaySessionDetailView(TeacherRequiredMixin, DetailView):
    template_name = 'teachers/today_session_detail.html'
    context_object_name = 'session'

    def get_queryset(self):
        return AttendanceSession.objects.filter(course__teacher=self.teacher).select_related(
            'course__subject', 'course__student_group', 'created_by'
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.date != timezone.now().date():
            return HttpResponseRedirect(
                reverse('teachers:session_detail', args=[self.object.pk])
            )
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = AttendanceFormSet(
            queryset=self.object.records.select_related('student')
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.date != timezone.now().date():
            return HttpResponseRedirect(
                reverse('teachers:session_detail', args=[self.object.pk])
            )
        formset = AttendanceFormSet(
            request.POST,
            queryset=self.object.records.select_related('student'),
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Asistencia guardada.')
            if request.htmx:
                return self._render_panel(request)
            return HttpResponseRedirect(request.get_full_path())
        context = self.get_context_data(object=self.object)
        context['formset'] = formset
        if request.htmx:
            return self._render_panel(request, context)
        return self.render_to_response(context)

    def _render_panel(self, request, context=None):
        if context is None:
            context = self.get_context_data(object=self.object)
        return render(
            request,
            'teachers/today_session_detail.html#attendance_panel',
            context,
        )


# --- Partial views (HTMX fragments) ---

class RecordToggleStatusView(TeacherRequiredMixin, View):
    """Today-page-only cyclic status button (D5)."""

    def post(self, request, *args, **kwargs):
        record = get_object_or_404(
            AttendanceRecord.objects.select_related('session__course__teacher'),
            pk=kwargs['pk'],
        )
        if record.session.course.teacher != self.teacher:
            return HttpResponseForbidden('No autorizado')

        record.status = STATUS_CYCLE.get(record.status, AttendanceRecord.Status.PRESENT)
        try:
            record.full_clean()
        except ValidationError as exc:
            context = {'record': record, 'errors': exc.message_dict}
            response = render(
                request,
                'teachers/today_session_detail.html#record_status_button',
                context,
            )
            return retarget(response, f'#record-status-{record.pk}')
        record.save(update_fields=['status', 'updated_at'])

        context = {'record': record}
        return render(
            request,
            'teachers/today_session_detail.html#record_status_button',
            context,
        )
