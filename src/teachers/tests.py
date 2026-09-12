from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

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

    def make_session(self, date='2026-09-10', course=None):
        course = course or self.course
        session = AttendanceSession.objects.create(
            course=course, date=date, created_by=course.teacher
        )
        create_attendance_records(session)
        return session

    # Session creation (CourseDetailView POST)

    def test_create_session(self):
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.post(url, {'date': '2026-09-15'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AttendanceSession.objects.filter(course=self.course, date='2026-09-15').exists()
        )

    def test_create_session_generates_records(self):
        url = reverse('teachers:course_detail', args=[self.course.pk])
        self.client.post(url, {'date': '2026-09-15'})
        session = AttendanceSession.objects.get(course=self.course, date='2026-09-15')
        self.assertEqual(session.records.count(), 1)

    def test_create_duplicate_session_date_rejected(self):
        self.make_session('2026-09-15')
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.post(url, {'date': '2026-09-15'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            AttendanceSession.objects.filter(course=self.course, date='2026-09-15').count(),
            1,
        )

    def test_other_teacher_cannot_create_session(self):
        self.client.force_login(self.other_user)
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.post(url, {'date': '2026-09-16'})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            AttendanceSession.objects.filter(course=self.course, date='2026-09-16').exists()
        )

    # Session update (SessionUpdateView)

    def test_edit_session(self):
        session = self.make_session('2026-09-10')
        url = reverse('teachers:session_edit', args=[session.pk])
        response = self.client.post(url, {'date': '2026-09-12'})
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        self.assertEqual(str(session.date), '2026-09-12')

    def test_edit_session_keeps_records(self):
        session = self.make_session('2026-09-10')
        url = reverse('teachers:session_edit', args=[session.pk])
        self.client.post(url, {'date': '2026-09-12'})
        session.refresh_from_db()
        self.assertEqual(session.records.count(), 1)

    def test_edit_session_respects_unique_date(self):
        self.make_session('2026-09-10')
        session2 = self.make_session('2026-09-11')
        url = reverse('teachers:session_edit', args=[session2.pk])
        response = self.client.post(url, {'date': '2026-09-10'})
        self.assertEqual(response.status_code, 200)
        session2.refresh_from_db()
        self.assertEqual(str(session2.date), '2026-09-11')

    def test_edit_session_renders_form_on_get(self):
        session = self.make_session('2026-09-10')
        url = reverse('teachers:session_edit', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2026-09-10')

    def test_other_teacher_cannot_edit_session(self):
        session = self.make_session('2026-09-10')
        self.client.force_login(self.other_user)
        url = reverse('teachers:session_edit', args=[session.pk])
        response = self.client.post(url, {'date': '2026-09-13'})
        self.assertEqual(response.status_code, 404)
        session.refresh_from_db()
        self.assertEqual(str(session.date), '2026-09-10')

    # Session deletion (SessionDeleteView)

    def test_delete_session(self):
        session = self.make_session('2026-09-10')
        url = reverse('teachers:session_delete', args=[session.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AttendanceSession.objects.filter(pk=session.pk).exists())

    def test_delete_session_removes_records(self):
        session = self.make_session('2026-09-10')
        url = reverse('teachers:session_delete', args=[session.pk])
        self.client.post(url)
        self.assertFalse(
            AttendanceRecord.objects.filter(session_id=session.pk).exists()
        )

    def test_other_teacher_cannot_delete_session(self):
        session = self.make_session('2026-09-10')
        self.client.force_login(self.other_user)
        url = reverse('teachers:session_delete', args=[session.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(AttendanceSession.objects.filter(pk=session.pk).exists())

    # Session detail (attendance notes saving)

    def test_save_notes_htmx(self):
        session = self.make_session('2026-09-10')
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
        session = self.make_session('2026-09-10')
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
