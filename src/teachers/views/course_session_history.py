from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView
from django_htmx.http import retarget

from school.models import AttendanceSession, Course, create_attendance_records

from ..forms import SessionForm
from .mixins import TeacherRequiredMixin, session_detail_url

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
        return self.course.sessions.exclude(date=timezone.now().date())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        context['form'] = SessionForm(course=self.course)
        return context

    def post(self, request, *args, **kwargs):
        self.course = self.get_course()
        form = SessionForm(request.POST, course=self.course)
        if form.is_valid():
            session = AttendanceSession.objects.create(
                course=self.course,
                date=form.cleaned_data['date'],
                created_by=self.teacher,
            )
            create_attendance_records(session)
            messages.success(request, 'Sesión creada.')
            if request.htmx:
                return HttpResponse(
                    status=200,
                    headers={'HX-Redirect': session_detail_url(session)},
                )
            return HttpResponseRedirect(session_detail_url(session))
        context = {
            'course': self.course,
            'form': form,
            self.context_object_name: self.get_queryset(),
        }
        if request.htmx:
            response = render(
                request,
                'teachers/course_session_history.html#session_create_form',
                context,
            )
            return retarget(response, '#session-form')
        return render(request, self.template_name, context)


# --- Partial views (HTMX fragments) ---


class SessionDeleteView(TeacherRequiredMixin, View):
    """Past-session deletes re-render the history list; today deletes redirect (D6)."""

    def post(self, request, *args, **kwargs):
        session = get_object_or_404(
            AttendanceSession.objects.select_related('course'),
            pk=kwargs['pk'],
            course__teacher=self.teacher,
        )
        course = session.course
        is_today = session.date == timezone.now().date()
        session.delete()
        messages.success(request, 'Sesión eliminada.')
        if request.htmx:
            if is_today:
                return HttpResponse(
                    status=200,
                    headers={
                        'HX-Redirect': reverse(
                            'teachers:course_detail', args=[course.pk]
                        )
                    },
                )
            context = {
                'course': course,
                'sessions': course.sessions.exclude(date=timezone.now().date()),
            }
            return render(
                request,
                'teachers/course_session_history.html#session_list',
                context,
            )
        return HttpResponseRedirect(
            reverse('teachers:course_session_history', args=[course.pk])
        )
