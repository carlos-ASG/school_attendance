from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView

from school.models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    create_attendance_records,
)

from ..forms import SessionForm
from .mixins import TeacherRequiredMixin

ATTENDED_STATUSES = (
    AttendanceRecord.Status.PRESENT,
    AttendanceRecord.Status.LATE,
    AttendanceRecord.Status.EXCUSED,
)


# --- Template views (full pages) ---

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
