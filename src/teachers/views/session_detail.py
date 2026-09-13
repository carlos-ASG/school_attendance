from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView
from django_htmx.http import retarget

from school.models import AttendanceRecord, AttendanceSession

from ..forms import AttendanceFormSet, SessionForm
from .mixins import TeacherRequiredMixin

STATUS_CYCLE = {
    AttendanceRecord.Status.PRESENT: AttendanceRecord.Status.ABSENT,
    AttendanceRecord.Status.ABSENT: AttendanceRecord.Status.LATE,
    AttendanceRecord.Status.LATE: AttendanceRecord.Status.EXCUSED,
    AttendanceRecord.Status.EXCUSED: AttendanceRecord.Status.PRESENT,
}


# --- Template views (full pages) ---

class SessionDetailView(TeacherRequiredMixin, DetailView):
    template_name = 'teachers/session_detail.html'
    context_object_name = 'session'

    def get_queryset(self):
        return AttendanceSession.objects.filter(course__teacher=self.teacher).select_related(
            'course__subject', 'course__student_group', 'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editable'] = (
            self.object.date == timezone.now().date()
        ) or (self.request.GET.get('edit') == '1')
        context['edit_mode'] = self.request.GET.get('edit') == '1'
        context['today'] = timezone.now().date()
        context['formset'] = AttendanceFormSet(
            queryset=self.object.records.select_related('student')
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = AttendanceFormSet(
            request.POST,
            queryset=self.object.records.select_related('student'),
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Attendance saved.')
            if request.htmx:
                return self._render_panel(request)
            return HttpResponseRedirect(request.get_full_path())
        context = self.get_context_data(object=self.object)
        context['formset'] = formset
        response = self._render_panel(request, context)
        if request.htmx:
            return retarget(response, '#attendance-panel')
        return response

    def _render_panel(self, request, context=None):
        if context is None:
            context = self.get_context_data(object=self.object)
        return render(
            request,
            'teachers/session_detail.html#attendance_panel',
            context,
        )


# --- Partial views (HTMX fragments) ---

class SessionMixin(TeacherRequiredMixin):
    def get_session(self, pk):
        return get_object_or_404(
            AttendanceSession.objects.select_related('course__teacher', 'created_by'),
            pk=pk,
            course__teacher=self.teacher,
        )


class RecordToggleStatusView(TeacherRequiredMixin, View):
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
                'teachers/session_detail.html#record_status_button',
                context,
            )
            return retarget(response, f'#record-status-{record.pk}')
        record.save(update_fields=['status', 'updated_at'])

        context = {'record': record}
        return render(
            request,
            'teachers/session_detail.html#record_status_button',
            context,
        )


class SessionUpdateView(SessionMixin, View):
    def get(self, request, *args, **kwargs):
        session = self.get_session(kwargs['pk'])
        form = SessionForm(initial={'date': session.date})
        context = {'session': session, 'course': session.course, 'form': form}
        return render(
            request, 'teachers/session_detail.html#session_form', context
        )

    def post(self, request, *args, **kwargs):
        session = self.get_session(kwargs['pk'])
        form = SessionForm(
            request.POST, course=session.course, exclude_pk=session.pk
        )
        if form.is_valid():
            session.date = form.cleaned_data['date']
            session.save(update_fields=['date', 'updated_at'])
            messages.success(request, 'Session updated.')
            if request.htmx:
                context = {
                    'session': session,
                    'editable': True,
                    'today': timezone.now().date(),
                }
                return render(
                    request,
                    'teachers/session_detail.html#session_header',
                    context,
                )
            return HttpResponseRedirect(
                reverse('teachers:session_detail', args=[session.pk])
            )
        context = {'session': session, 'course': session.course, 'form': form}
        response = render(
            request, 'teachers/session_detail.html#session_form', context
        )
        if request.htmx:
            return retarget(response, '#session-edit')
        return response


class SessionDeleteView(SessionMixin, View):
    def post(self, request, *args, **kwargs):
        session = self.get_session(kwargs['pk'])
        session.delete()
        messages.success(request, 'Session deleted.')
        if request.htmx:
            return HttpResponse(status=200, headers={
                'HX-Redirect': reverse('teachers:course_session_history', args=[session.course_id]),
            })
        return HttpResponseRedirect(
            reverse('teachers:course_session_history', args=[session.course_id])
        )
