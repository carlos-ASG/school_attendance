from typing import Any

from django.db.models import Count

from ..models import AttendanceRecord, Course, Student


def get_course_attendance_summary(*, course: Course) -> dict[int, dict[str, Any]]:
    """Return a lookup dict keyed by student pk with attendance summary.

    Counts PRESENT, LATE and EXCUSED records as attended, using the total
    number of sessions for the course as the denominator. Issues at most
    two queries regardless of the number of students.
    """
    students = course.student_group.students.all()
    total = course.sessions.count()
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
            session__course=course,
            status__in=AttendanceRecord.ATTENDED_STATUSES,
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


def get_student_attendance_summary(
    *, course: Course, student: Student
) -> dict[str, Any]:
    """Return the single-student summary: attended / total sessions (D3)."""
    total = course.sessions.count()
    if total == 0:
        return {'attended': 0, 'total': 0, 'percentage': '0'}
    attended = AttendanceRecord.objects.filter(
        session__course=course,
        student=student,
        status__in=AttendanceRecord.ATTENDED_STATUSES,
    ).count()
    return {
        'attended': attended,
        'total': total,
        'percentage': f'{attended / total * 100:.1f}',
    }
