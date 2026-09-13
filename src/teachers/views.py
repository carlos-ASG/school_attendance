from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView
from django_htmx.http import retarget

from school.models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    Teacher,
    create_attendance_records,
)

from .forms import AttendanceFormSet, SessionForm

STATUS_CYCLE = {
    AttendanceRecord.Status.PRESENT: AttendanceRecord.Status.ABSENT,
    AttendanceRecord.Status.ABSENT: AttendanceRecord.Status.LATE,
    AttendanceRecord.Status.LATE: AttendanceRecord.Status.EXCUSED,
    AttendanceRecord.Status.EXCUSED: AttendanceRecord.Status.PRESENT,
}

ATTENDED_STATUSES = (
    AttendanceRecord.Status.PRESENT,
    AttendanceRecord.Status.LATE,
    AttendanceRecord.Status.EXCUSED,
)


def get_teacher(request):
    """Return the Teacher linked to the request user, or None."""
    if request.user.is_authenticated:
        return Teacher.objects.filter(user=request.user).first()
    return None


class TeacherRequiredMixin:
    """Allow access only to authenticated users linked to a Teacher."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse_lazy('teachers:login'))
        self.teacher = get_teacher(request)
        if self.teacher is None:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class LoginView(auth_views.LoginView):
    template_name = 'teachers/login.html'

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse('admin:index')
        return reverse('teachers:dashboard')


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('teachers:login')


class HomeRedirectView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('teachers:login')
        if request.user.is_staff:
            return redirect('admin:index')
        return redirect('teachers:dashboard')


class DashboardView(TeacherRequiredMixin, ListView):
    template_name = 'teachers/dashboard.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return (
            Course.objects.filter(teacher=self.teacher)
            .select_related('subject', 'teacher', 'student_group')
            .annotate(student_count=Count('student_group__students'))
        )


class CourseDetailView(TeacherRequiredMixin, DetailView):
    template_name = 'teachers/course_detail.html'
    context_object_name = 'course'

    def get_queryset(self):
        return (
            Course.objects.filter(teacher=self.teacher)
            .select_related('subject', 'teacher', 'student_group')
            .prefetch_related('student_group__students', 'schedule_slots')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attendance'] = self.get_attendance_summary()
        context['form'] = self.session_form
        context['today_session'] = self.object.sessions.filter(
            date=timezone.now().date()
        ).first()
        return context

    def get_attendance_summary(self):
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

    def dispatch(self, request, *args, **kwargs):
        self.session_form = None
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'create_today' in request.POST:
            return self._create_today_session(request)
        form = SessionForm(request.POST, course=self.object)
        if form.is_valid():
            session = AttendanceSession.objects.create(
                course=self.object,
                date=form.cleaned_data['date'],
                created_by=self.teacher,
            )
            create_attendance_records(session)
            messages.success(request, 'Session created.')
            return HttpResponseRedirect(
                reverse('teachers:session_detail', args=[session.pk])
            )
        self.session_form = form
        context = self.get_context_data(object=self.object)
        return render(request, self.template_name, context)

    def _create_today_session(self, request):
        today = timezone.now().date()
        session = self.object.sessions.filter(date=today).first()
        if session is None:
            session = AttendanceSession.objects.create(
                course=self.object,
                date=today,
                created_by=self.teacher,
            )
            create_attendance_records(session)
            messages.success(request, 'Session created.')
        return HttpResponseRedirect(
            reverse('teachers:session_detail', args=[session.pk])
        )


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
        return render(request, 'teachers/partials/attendance_panel.html', context)


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
            response = render(request, 'teachers/partials/record_status_button.html', context)
            return retarget(response, f'#record-status-{record.pk}')
        record.save(update_fields=['status', 'updated_at'])

        context = {'record': record}
        return render(request, 'teachers/partials/record_status_button.html', context)


class SessionMixin(TeacherRequiredMixin):
    def get_session(self, pk):
        return get_object_or_404(
            AttendanceSession.objects.select_related('course__teacher', 'created_by'),
            pk=pk,
            course__teacher=self.teacher,
        )


class SessionUpdateView(SessionMixin, View):
    def get(self, request, *args, **kwargs):
        session = self.get_session(kwargs['pk'])
        form = SessionForm(initial={'date': session.date})
        context = {'session': session, 'course': session.course, 'form': form}
        return render(request, 'teachers/partials/session_form.html', context)

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
                    request, 'teachers/partials/session_header.html', context
                )
            return HttpResponseRedirect(
                reverse('teachers:session_detail', args=[session.pk])
            )
        context = {'session': session, 'course': session.course, 'form': form}
        response = render(request, 'teachers/partials/session_form.html', context)
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
