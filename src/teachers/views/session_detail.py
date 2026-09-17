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

from ..forms import AttendanceEditFormSet
from .mixins import TeacherRequiredMixin


# --- Template views (full pages) ---

class PreviousSessionDetailView(TeacherRequiredMixin, DetailView):
    """Read-only review of a past session, with a batch edit form (D5)."""

    template_name = 'teachers/previous_session_detail.html'
    context_object_name = 'session'

    def get_queryset(self) -> QuerySet[AttendanceSession]:
        return AttendanceSession.objects.filter(course__teacher=self.teacher).select_related(
            'course__subject', 'course__student_group', 'created_by'
        )

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        if self.object.date == timezone.now().date():
            return HttpResponseRedirect(
                reverse('teachers:today_session_detail', args=[self.object.pk])
            )
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['edit_mode'] = self.request.GET.get('edit') == '1'
        if context['edit_mode']:
            context['formset'] = AttendanceEditFormSet(
                queryset=self.object.records.select_related('student')
            )
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        if self.object.date == timezone.now().date():
            return HttpResponseRedirect(
                reverse('teachers:today_session_detail', args=[self.object.pk])
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
                reverse('teachers:session_detail', args=[self.object.pk])
            )
        context = self.get_context_data(object=self.object)
        context['edit_mode'] = True
        context['formset'] = formset
        if request.htmx:
            response = render(
                request,
                'teachers/previous_session_detail.html#attendance_edit_form',
                context,
            )
            return retarget(response, '#attendance-panel')
        return self.render_to_response(context)

    def _render_readonly(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            'teachers/previous_session_detail.html#attendance_readonly',
            {
                'session': self.object,
            },
        )
