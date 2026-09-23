from typing import Any

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView
from django_htmx.http import retarget

from school.models import AttendanceSession
from school.selectors import teacher_sessions

from ..forms import AttendanceEditFormSet
from .mixins import TeacherRequiredMixin

# --- Template views (full pages) ---

class PreviousSessionDetailView(TeacherRequiredMixin, DetailView):
    """Read-only review of a past session, with a batch edit form (D5)."""

    template_name = 'teacher_panel/previous_session_detail.html'
    context_object_name = 'session'

    def get_queryset(self) -> QuerySet[AttendanceSession]:
        return teacher_sessions(teacher=self.teacher)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        if self.object.date == timezone.now().date():
            return HttpResponseRedirect(
                reverse('teacher_panel:today_session_detail', args=[self.object.pk])
            )
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['session_is_editable'] = not self.object.is_frozen()
        context['edit_mode'] = (
            context['session_is_editable'] and self.request.GET.get('edit') == '1'
        )
        if context['edit_mode']:
            context['formset'] = AttendanceEditFormSet(
                queryset=self.object.records.select_related('student')
            )
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        if self.object.date == timezone.now().date():
            return HttpResponseRedirect(
                reverse('teacher_panel:today_session_detail', args=[self.object.pk])
            )
        if self.object.is_frozen():
            messages.error(request, AttendanceSession.FROZEN_MESSAGE)
            if request.htmx:
                return retarget(self._render_readonly(request), '#attendance-panel')
            return HttpResponseRedirect(
                reverse('teacher_panel:session_detail', args=[self.object.pk])
            )
        formset = AttendanceEditFormSet(
            request.POST,
            queryset=self.object.records.select_related('student'),
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Cambios guardados.')
            if request.htmx:
                return self._render_readonly(request)
            return HttpResponseRedirect(
                reverse('teacher_panel:session_detail', args=[self.object.pk])
            )
        context = self.get_context_data(object=self.object)
        context['edit_mode'] = True
        context['formset'] = formset
        if request.htmx:
            response = render(
                request,
                'teacher_panel/previous_session_detail.html#attendance_edit_form',
                context,
            )
            return retarget(response, '#attendance-panel')
        return self.render_to_response(context)

    def _render_readonly(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            'teacher_panel/previous_session_detail.html#attendance_readonly',
            {
                'session': self.object,
            },
        )
