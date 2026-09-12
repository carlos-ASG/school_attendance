from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from school.models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    Student,
    StudentGroup,
    Subject,
    Teacher,
    create_attendance_records,
)


def days_from_today(days):
    return (timezone.now().date() + timedelta(days=days)).isoformat()


class TeacherSessionViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)

        cls.teacher_user = User.objects.create_user('profe1', password='pass')
        cls.other_user = User.objects.create_user('profe2', password='pass')

        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.other_teacher = Teacher.objects.create(
            first_name='Luis', last_name='Martínez', user=cls.other_user
        )

        cls.subject = Subject.objects.create(name='Ciencias')
        cls.course = Course.objects.create(
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )
        cls.other_course = Course.objects.create(
            student_group=cls.group, teacher=cls.other_teacher, subject=cls.subject
        )

    def setUp(self):
        self.client.force_login(self.teacher_user)

    def make_session(self, date=None, course=None):
        course = course or self.course
        session = AttendanceSession.objects.create(
            course=course, date=date or days_from_today(-1), created_by=course.teacher
        )
        create_attendance_records(session)
        return session

    # Session creation (CourseDetailView POST)

    def test_create_session(self):
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(-1)
            ).exists()
        )

    def test_create_session_generates_records(self):
        url = reverse('teachers:course_detail', args=[self.course.pk])
        self.client.post(url, {'date': days_from_today(-1)})
        session = AttendanceSession.objects.get(
            course=self.course, date=days_from_today(-1)
        )
        self.assertEqual(session.records.count(), 1)

    def test_create_future_session_rejected(self):
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(1)})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(1)
            ).exists()
        )
        self.assertContains(response, 'no puede ser posterior')

    def test_create_duplicate_session_date_rejected(self):
        self.make_session(days_from_today(-1))
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(-1)
            ).count(),
            1,
        )

    def test_other_teacher_cannot_create_session(self):
        self.client.force_login(self.other_user)
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(-1)
            ).exists()
        )

    # Session update (SessionUpdateView)

    def test_edit_session(self):
        session = self.make_session(days_from_today(-2))
        url = reverse('teachers:session_edit', args=[session.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        self.assertEqual(str(session.date), days_from_today(-1))

    def test_edit_session_keeps_records(self):
        session = self.make_session(days_from_today(-2))
        url = reverse('teachers:session_edit', args=[session.pk])
        self.client.post(url, {'date': days_from_today(-1)})
        session.refresh_from_db()
        self.assertEqual(session.records.count(), 1)

    def test_edit_session_respects_unique_date(self):
        self.make_session(days_from_today(-2))
        session2 = self.make_session(days_from_today(-1))
        url = reverse('teachers:session_edit', args=[session2.pk])
        response = self.client.post(url, {'date': days_from_today(-2)})
        self.assertEqual(response.status_code, 200)
        session2.refresh_from_db()
        self.assertEqual(str(session2.date), days_from_today(-1))

    def test_edit_session_renders_form_on_get(self):
        session = self.make_session(days_from_today(-2))
        url = reverse('teachers:session_edit', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, days_from_today(-2))

    def test_other_teacher_cannot_edit_session(self):
        session = self.make_session(days_from_today(-2))
        self.client.force_login(self.other_user)
        url = reverse('teachers:session_edit', args=[session.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 404)
        session.refresh_from_db()
        self.assertEqual(str(session.date), days_from_today(-2))

    # Session deletion (SessionDeleteView)

    def test_delete_session(self):
        session = self.make_session(days_from_today(-2))
        url = reverse('teachers:session_delete', args=[session.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AttendanceSession.objects.filter(pk=session.pk).exists())

    def test_delete_session_removes_records(self):
        session = self.make_session(days_from_today(-2))
        url = reverse('teachers:session_delete', args=[session.pk])
        self.client.post(url)
        self.assertFalse(
            AttendanceRecord.objects.filter(session_id=session.pk).exists()
        )

    def test_other_teacher_cannot_delete_session(self):
        session = self.make_session(days_from_today(-2))
        self.client.force_login(self.other_user)
        url = reverse('teachers:session_delete', args=[session.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(AttendanceSession.objects.filter(pk=session.pk).exists())

    # Session detail (attendance notes saving)

    def test_save_notes_htmx(self):
        session = self.make_session(days_from_today(-2))
        record = session.records.first()
        url = reverse('teachers:session_detail', args=[session.pk])
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            f'form-0-id': str(record.pk),
            f'form-0-notes': 'Llegó tarde',
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.notes, 'Llegó tarde')

    def test_save_notes_without_htmx_redirects(self):
        session = self.make_session(days_from_today(-2))
        record = session.records.first()
        url = reverse('teachers:session_detail', args=[session.pk])
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': str(record.pk),
            'form-0-notes': 'Sin HTMX',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        record.refresh_from_db()
        self.assertEqual(record.notes, 'Sin HTMX')


class CourseDetailViewAttendanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudentGroup.objects.create(name='Grupo Asistencia')
        cls.student_a = Student.objects.create(
            first_name='Ana', paternal_surname='Pérez', maternal_surname='López'
        )
        cls.student_b = Student.objects.create(
            first_name='Beto', paternal_surname='García', maternal_surname='Ruiz'
        )
        cls.group.students.add(cls.student_a, cls.student_b)

        cls.teacher_user = User.objects.create_user('profe3', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Marta', last_name='López', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Historia')
        cls.course = Course.objects.create(
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self):
        self.client.force_login(self.teacher_user)

    def make_session(self, date=None):
        session = AttendanceSession.objects.create(
            course=self.course, date=date or days_from_today(-1), created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def set_status(self, session, student, status):
        record = session.records.get(student=student)
        record.status = status
        record.save(update_fields=['status'])

    def test_no_sessions_shows_zero_attendance(self):
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        attendance = response.context['attendance']
        self.assertEqual(attendance[self.student_a.pk]['attended'], 0)
        self.assertEqual(attendance[self.student_a.pk]['total'], 0)
        self.assertEqual(attendance[self.student_a.pk]['percentage'], '0')

    def test_mixed_statuses_counted_as_attended(self):
        session1 = self.make_session(days_from_today(-2))
        session2 = self.make_session(days_from_today(-1))
        self.set_status(session1, self.student_a, AttendanceRecord.Status.PRESENT)
        self.set_status(session2, self.student_a, AttendanceRecord.Status.ABSENT)
        self.set_status(session1, self.student_b, AttendanceRecord.Status.LATE)
        self.set_status(session2, self.student_b, AttendanceRecord.Status.EXCUSED)

        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        attendance = response.context['attendance']
        self.assertEqual(attendance[self.student_a.pk]['attended'], 1)
        self.assertEqual(attendance[self.student_a.pk]['total'], 2)
        self.assertEqual(attendance[self.student_a.pk]['percentage'], '50.0')
        self.assertEqual(attendance[self.student_b.pk]['attended'], 2)
        self.assertEqual(attendance[self.student_b.pk]['percentage'], '100.0')

    def test_all_absent_shows_zero_percentage(self):
        session = self.make_session()
        self.set_status(session, self.student_a, AttendanceRecord.Status.ABSENT)
        self.set_status(session, self.student_b, AttendanceRecord.Status.ABSENT)

        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        attendance = response.context['attendance']
        self.assertEqual(attendance[self.student_a.pk]['percentage'], '0.0')

    def test_other_course_records_not_counted(self):
        other_group = StudentGroup.objects.create(name='Grupo Otro')
        other_group.students.add(self.student_a)
        other_subject = Subject.objects.create(name='Geografía')
        other_course = Course.objects.create(
            student_group=other_group, teacher=self.teacher, subject=other_subject
        )
        other_session = AttendanceSession.objects.create(
            course=other_course, date=days_from_today(-1), created_by=self.teacher
        )
        create_attendance_records(other_session)

        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        attendance = response.context['attendance']
        self.assertEqual(attendance[self.student_a.pk]['attended'], 0)
        self.assertEqual(attendance[self.student_a.pk]['total'], 0)

    def test_template_renders_attendance_table(self):
        session1 = self.make_session(days_from_today(-2))
        session2 = self.make_session(days_from_today(-1))
        self.set_status(session1, self.student_a, AttendanceRecord.Status.PRESENT)
        self.set_status(session2, self.student_a, AttendanceRecord.Status.ABSENT)
        self.set_status(session1, self.student_b, AttendanceRecord.Status.ABSENT)
        self.set_status(session2, self.student_b, AttendanceRecord.Status.ABSENT)

        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        self.assertContains(response, '<th>Estudiante</th>')
        self.assertContains(response, '<th>Asistencia</th>')
        self.assertContains(response, '1/2 (50.0%)')
        self.assertContains(response, '0/2 (0.0%)')
