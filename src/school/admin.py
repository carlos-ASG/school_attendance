from datetime import date, timedelta
from typing import Any

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.models import BaseInlineFormSet
from django.http import HttpRequest
from django.urls import path
from django.urls.resolvers import URLPattern
from django.views.generic import TemplateView
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.views import UnfoldModelAdminViewMixin

from .models import (
    AttendanceRecord,
    AttendanceSession,
    ClassSchedule,
    Course,
    NonSchoolDay,
    SchoolCycle,
    Student,
    StudentGroup,
    Subject,
    Teacher,
    create_attendance_records,
)
from .resources import StudentResource


@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_classes = [StudentResource]
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('first_name', 'paternal_surname', 'maternal_surname', 'email')
    search_fields = ('first_name', 'paternal_surname', 'maternal_surname', 'email')
    list_filter = ('student_groups',)


@admin.register(Teacher)
class TeacherAdmin(ModelAdmin):
    list_display = ('first_name', 'last_name', 'user')
    search_fields = ('first_name', 'last_name')
    list_filter = ('user',)


@admin.register(Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(StudentGroup)
class StudentGroupAdmin(ModelAdmin):
    list_display = ('name', 'student_count')
    search_fields = ('name',)
    filter_horizontal = ('students',)

    @admin.display(description='Estudiantes')
    def student_count(self, obj: Student) -> int:
        return obj.students.count()


class ClassScheduleInline(TabularInline):
    model = ClassSchedule
    extra = 1


class NonSchoolDayInline(TabularInline):
    model = NonSchoolDay
    extra = 1


@admin.register(SchoolCycle)
class SchoolCycleAdmin(ModelAdmin):
    list_display = ('name', 'cycle_type', 'start_date', 'end_date')
    list_filter = ('cycle_type',)
    search_fields = ('name',)
    inlines = [NonSchoolDayInline]


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ('subject', 'teacher', 'student_group', 'school_cycle', 'classroom', 'student_count')
    list_filter = ('subject', 'teacher', 'student_group', 'school_cycle')
    search_fields = (
        'subject__name',
        'teacher__first_name',
        'teacher__last_name',
        'student_group__name',
        'school_cycle__name',
    )
    inlines = [ClassScheduleInline]

    @admin.display(description='Estudiantes')
    def student_count(self, obj: Course) -> int:
        return obj.student_group.students.count()


class AttendanceRecordInline(TabularInline):
    model = AttendanceRecord
    extra = 0

    def formfield_for_foreignkey(
        self, db_field: models.Field, request: HttpRequest, **kwargs: Any
    ) -> forms.Field:
        if db_field.name == 'student':
            session = self.get_session(request)
            if session is None:
                kwargs['queryset'] = Student.objects.none()
            else:
                kwargs['queryset'] = session.course.student_group.students.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_session(self, request: HttpRequest) -> AttendanceSession | None:
        try:
            object_id = request.resolver_match.kwargs.get('object_id')
        except (AttributeError, KeyError):
            return None
        if object_id is None:
            return None
        try:
            return AttendanceSession.objects.get(pk=object_id)
        except (AttendanceSession.DoesNotExist, ValueError, TypeError):
            return None


class ReportsFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Desde',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    end_date = forms.DateField(
        label='Hasta',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )


class ReportsView(UnfoldModelAdminViewMixin, TemplateView):
    template_name = 'admin/school/attendancesession/reports.html'
    title = 'Reportes de asistencia'
    permission_required = ()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        today = date.today()
        default_start = today - timedelta(days=30)
        default_end = today

        form = ReportsFilterForm(self.request.GET or None)
        start, end = default_start, default_end
        if form.is_valid():
            start = form.cleaned_data.get('start_date') or default_start
            end = form.cleaned_data.get('end_date') or default_end

        context.update(
            {
                'form': form,
                'start': start,
                'end': end,
                'students_count': Student.objects.count(),
                'courses_count': Course.objects.count(),
                'sessions_count': AttendanceSession.objects.filter(
                    date__range=(start, end)
                ).count(),
            }
        )
        return context


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(ModelAdmin):
    list_display = ('course', 'date', 'created_by', 'created_at')
    list_filter = ('course', 'date', 'created_by')
    inlines = [AttendanceRecordInline]

    def get_urls(self) -> list[URLPattern]:
        return [
            path(
                'reports/',
                self.admin_site.admin_view(ReportsView.as_view(model_admin=self)),
                name='school_attendancesession_reports',
            ),
        ] + super().get_urls()

    def save_related(
        self,
        request: HttpRequest,
        form: forms.ModelForm,
        formsets: list[BaseInlineFormSet],
        change: bool,
    ) -> None:
        super().save_related(request, form, formsets, change)
        create_attendance_records(form.instance)


admin.site.site_header = 'Administración de Asistencia Escolar'
