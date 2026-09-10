from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView

from .forms import AttendanceFormSet, SessionCreateForm
from .models import (
    AttendanceRecord,
    AttendanceSession,
    Classroom,
    Teacher,
    create_attendance_records,
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
            return redirect_to_login(request.get_full_path(), reverse_lazy('school:login'))
        self.teacher = get_teacher(request)
        if self.teacher is None:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class LoginView(auth_views.LoginView):
    template_name = 'school/login.html'

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse('admin:index')
        return reverse('school:dashboard')


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('school:login')


class HomeRedirectView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('school:login')
        if request.user.is_staff:
            return redirect('admin:index')
        return redirect('school:dashboard')


class DashboardView(TeacherRequiredMixin, ListView):
    template_name = 'school/dashboard.html'
    context_object_name = 'classrooms'

    def get_queryset(self):
        return (
            Classroom.objects.filter(teacher=self.teacher)
            .select_related('subject', 'teacher', 'student_group')
            .annotate(student_count=Count('student_group__students'))
        )


class ClassroomDetailView(TeacherRequiredMixin, DetailView):
    template_name = 'school/classroom_detail.html'
    context_object_name = 'classroom'

    def get_queryset(self):
        return (
            Classroom.objects.filter(teacher=self.teacher)
            .select_related('subject', 'teacher', 'student_group')
            .prefetch_related('student_group__students', 'schedule_slots')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sessions'] = self.object.sessions.all()[:20]
        context['form'] = self.session_form
        return context

    def dispatch(self, request, *args, **kwargs):
        self.session_form = None
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SessionCreateForm(request.POST, classroom=self.object)
        if form.is_valid():
            session = AttendanceSession.objects.create(
                classroom=self.object,
                date=form.cleaned_data['date'],
                created_by=self.teacher,
            )
            create_attendance_records(session)
            messages.success(request, 'Session created.')
        self.session_form = form
        return self._render_panel(request)

    def _render_panel(self, request):
        context = self.get_context_data(object=self.object)
        context['sessions'] = self.object.sessions.all()[:20]
        return render(request, 'school/partials/session_panel.html', context)


class SessionDetailView(TeacherRequiredMixin, DetailView):
    template_name = 'school/session_detail.html'
    context_object_name = 'session'

    def get_queryset(self):
        return AttendanceSession.objects.filter(classroom__teacher=self.teacher).select_related(
            'classroom__subject', 'classroom__student_group', 'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
            return self._render_panel(request)
        context = self.get_context_data(object=self.object)
        context['formset'] = formset
        return self._render_panel(request, context)

    def _render_panel(self, request, context=None):
        if context is None:
            context = self.get_context_data(object=self.object)
        return render(request, 'school/partials/attendance_panel.html', context)
