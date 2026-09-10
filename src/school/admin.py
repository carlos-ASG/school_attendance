from django.contrib import admin

from .models import (
    AttendanceRecord,
    AttendanceSession,
    Classroom,
    ClassSchedule,
    Student,
    StudentGroup,
    Subject,
    Teacher,
    create_attendance_records,
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('student_groups',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'user')
    search_fields = ('first_name', 'last_name')
    list_filter = ('user',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_count')
    search_fields = ('name',)
    filter_horizontal = ('students',)

    @admin.display(description='Students')
    def student_count(self, obj):
        return obj.students.count()


class ClassScheduleInline(admin.TabularInline):
    model = ClassSchedule
    extra = 1


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('subject', 'teacher', 'student_group', 'student_count')
    list_filter = ('subject', 'teacher', 'student_group')
    search_fields = ('subject__name', 'teacher__first_name', 'teacher__last_name', 'student_group__name')
    inlines = [ClassScheduleInline]

    @admin.display(description='Students')
    def student_count(self, obj):
        return obj.student_group.students.count()


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'date', 'created_by', 'created_at')
    list_filter = ('classroom', 'date', 'created_by')
    inlines = [AttendanceRecordInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        create_attendance_records(obj)


admin.site.site_header = 'School Attendance Administration'
