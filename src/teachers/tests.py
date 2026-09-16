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


class TodaySessionCreateViewTests(TestCase):
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

    def setUp(self):
        self.client.force_login(self.teacher_user)

    def test_create_today_session_redirects_to_today_detail(self):
        url = reverse('teachers:today_session_create', args=[self.course.pk])
        response = self.client.post(url)
        session = AttendanceSession.objects.get(
            course=self.course, date=days_from_today(0)
        )
        self.assertRedirects(
            response,
            reverse('teachers:today_session_detail', args=[session.pk]),
        )

    def test_create_today_session_generates_records(self):
        url = reverse('teachers:today_session_create', args=[self.course.pk])
        self.client.post(url)
        session = AttendanceSession.objects.get(
            course=self.course, date=days_from_today(0)
        )
        self.assertEqual(session.records.count(), 1)

    def test_create_today_existing_session_no_duplicate(self):
        session = AttendanceSession.objects.create(
            course=self.course, date=days_from_today(0), created_by=self.teacher
        )
        create_attendance_records(session)
        url = reverse('teachers:today_session_create', args=[self.course.pk])
        response = self.client.post(url)
        self.assertEqual(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(0)
            ).count(),
            1,
        )
        self.assertRedirects(
            response,
            reverse('teachers:today_session_detail', args=[session.pk]),
        )

    def test_get_not_allowed(self):
        url = reverse('teachers:today_session_create', args=[self.course.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_other_teacher_cannot_create_today_session(self):
        self.client.force_login(self.other_user)
        url = reverse('teachers:today_session_create', args=[self.course.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(0)
            ).exists()
        )


class SessionUrlGuardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = User.objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.course = Course.objects.create(
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self):
        self.client.force_login(self.teacher_user)

    def make_session(self, date):
        session = AttendanceSession.objects.create(
            course=self.course, date=date, created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def test_today_url_for_past_session_redirects(self):
        session = self.make_session(days_from_today(-1))
        url = reverse('teachers:today_session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse('teachers:session_detail', args=[session.pk]),
            fetch_redirect_response=False,
        )

    def test_previous_url_for_today_session_redirects(self):
        session = self.make_session(days_from_today(0))
        url = reverse('teachers:session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse('teachers:today_session_detail', args=[session.pk]),
            fetch_redirect_response=False,
        )

    def test_other_teacher_cannot_open_session(self):
        other_user = User.objects.create_user('profe2', password='pass')
        Teacher.objects.create(
            first_name='Luis', last_name='Martínez', user=other_user
        )
        self.client.force_login(other_user)
        session = self.make_session(days_from_today(-1))
        url = reverse('teachers:session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class CourseSessionHistoryViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = User.objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.course = Course.objects.create(
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self):
        self.client.force_login(self.teacher_user)

    def test_list_excludes_today_session(self):
        today_session = AttendanceSession.objects.create(
            course=self.course, date=days_from_today(0), created_by=self.teacher
        )
        create_attendance_records(today_session)
        past_session = AttendanceSession.objects.create(
            course=self.course, date=days_from_today(-1), created_by=self.teacher
        )
        create_attendance_records(past_session)
        url = reverse('teachers:course_session_history', args=[self.course.pk])
        response = self.client.get(url)
        sessions = list(response.context['sessions'])
        self.assertIn(past_session, sessions)
        self.assertNotIn(today_session, sessions)

    def test_create_past_session_redirects_to_previous_page(self):
        url = reverse('teachers:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        session = AttendanceSession.objects.get(
            course=self.course, date=days_from_today(-1)
        )
        self.assertRedirects(
            response, reverse('teachers:session_detail', args=[session.pk])
        )
        self.assertEqual(session.records.count(), 1)

    def test_create_today_date_rejected(self):
        url = reverse('teachers:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(0)})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(0)
            ).exists()
        )
        self.assertContains(response, 'Sesión de hoy')

    def test_create_future_session_rejected(self):
        url = reverse('teachers:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(1)})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(1)
            ).exists()
        )
        self.assertContains(response, 'no puede ser posterior')

    def test_create_duplicate_session_date_rejected(self):
        AttendanceSession.objects.create(
            course=self.course, date=days_from_today(-1), created_by=self.teacher
        )
        url = reverse('teachers:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(-1)
            ).count(),
            1,
        )

    def test_create_htmx_error_returns_form_fragment(self):
        url = reverse('teachers:course_session_history', args=[self.course.pk])
        response = self.client.post(
            url, {'date': days_from_today(1)}, HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no puede ser posterior')
        self.assertIn('HX-Retarget', response.headers)
        self.assertEqual(response.headers['HX-Retarget'], '#session-create')

    def test_create_htmx_success_redirects_via_hx_redirect(self):
        url = reverse('teachers:course_session_history', args=[self.course.pk])
        response = self.client.post(
            url, {'date': days_from_today(-1)}, HTTP_HX_REQUEST='true'
        )
        session = AttendanceSession.objects.get(
            course=self.course, date=days_from_today(-1)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Redirect', response.headers)
        self.assertEqual(
            response.headers['HX-Redirect'],
            reverse('teachers:session_detail', args=[session.pk]),
        )

    def test_other_teacher_cannot_create_session(self):
        other_user = User.objects.create_user('profe2', password='pass')
        Teacher.objects.create(
            first_name='Luis', last_name='Martínez', user=other_user
        )
        self.client.force_login(other_user)
        url = reverse('teachers:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(-1)
            ).exists()
        )


class PreviousSessionDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = User.objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
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

    def formset_data(self, session, **overrides):
        record = session.records.first()
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': str(record.pk),
        }
        data.update(overrides)
        return data

    def test_past_session_opens_read_only(self):
        session = self.make_session()
        url = reverse('teachers:session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Presente')
        self.assertNotContains(response, '<select')

    def test_edit_mode_renders_batch_form(self):
        session = self.make_session()
        url = reverse('teachers:session_detail', args=[session.pk])
        response = self.client.get(url, {'edit': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="form-0-status"')
        self.assertContains(response, 'Guardar cambios')

    def test_batch_edit_saves_all_rows(self):
        session = self.make_session()
        record = session.records.first()
        url = reverse('teachers:session_detail', args=[session.pk])
        response = self.client.post(
            url,
            self.formset_data(
                session, **{'form-0-status': 'ABSENT', 'form-0-notes': 'Llegó tarde'}
            ),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceRecord.Status.ABSENT)
        self.assertEqual(record.notes, 'Llegó tarde')

    def test_batch_edit_htmx_returns_readonly_fragment(self):
        session = self.make_session()
        url = reverse('teachers:session_detail', args=[session.pk])
        response = self.client.post(
            url,
            self.formset_data(session, **{'form-0-status': 'LATE'}),
            HTTP_HX_REQUEST='true',
        )
        self.assertContains(response, 'Cambios guardados')
        self.assertNotContains(response, '<select')

    def test_batch_edit_without_htmx_redirects_to_readonly(self):
        session = self.make_session()
        url = reverse('teachers:session_detail', args=[session.pk])
        response = self.client.post(
            url, self.formset_data(session, **{'form-0-status': 'EXCUSED'})
        )
        self.assertEqual(response.status_code, 302)

    def test_batch_edit_invalid_renders_form_with_errors(self):
        session = self.make_session()
        url = reverse('teachers:session_detail', args=[session.pk])
        response = self.client.post(
            url,
            self.formset_data(session, **{'form-0-status': 'BOGUS'}),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form-0-status')
        record = session.records.first()
        record.refresh_from_db()
        self.assertNotEqual(record.status, 'BOGUS')


class TodaySessionDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = User.objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.course = Course.objects.create(
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self):
        self.client.force_login(self.teacher_user)

    def make_today_session(self):
        session = AttendanceSession.objects.create(
            course=self.course, date=days_from_today(0), created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def test_today_page_renders_editable(self):
        session = self.make_today_session()
        url = reverse('teachers:today_session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'status-btn')
        self.assertContains(response, 'Guardar cambios')
        self.assertContains(response, 'x-data="attendancePanel"')
        self.assertContains(response, 'attendance-records-data')
        self.assertContains(response, reverse('api:update_session_records', args=[session.pk]))
        self.assertNotContains(response, '?edit=1')

    def test_post_no_longer_saves(self):
        """Per-action save was removed: the page is GET-only (batch save via API)."""
        session = self.make_today_session()
        record = session.records.first()
        url = reverse('teachers:today_session_detail', args=[session.pk])
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': str(record.pk),
            'form-0-notes': 'Llegó tarde',
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 405)
        record.refresh_from_db()
        self.assertEqual(record.notes, '')




class SessionDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = User.objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.course = Course.objects.create(
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self):
        self.client.force_login(self.teacher_user)

    def make_session(self, date):
        session = AttendanceSession.objects.create(
            course=self.course, date=date, created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def test_delete_past_session_htmx_renders_list_fragment(self):
        session = self.make_session(days_from_today(-2))
        url = reverse('teachers:session_delete', args=[session.pk])
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AttendanceSession.objects.filter(pk=session.pk).exists())
        self.assertFalse(
            AttendanceRecord.objects.filter(session_id=session.pk).exists()
        )
        self.assertContains(response, 'Aún no hay sesiones registradas.')

    def test_delete_last_session_shows_empty_state(self):
        session = self.make_session(days_from_today(-1))
        url = reverse('teachers:session_delete', args=[session.pk])
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertContains(response, 'Aún no hay sesiones registradas.')

    def test_delete_today_session_htmx_redirects_to_course_detail(self):
        session = self.make_session(days_from_today(0))
        url = reverse('teachers:session_delete', args=[session.pk])
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Redirect', response.headers)
        self.assertEqual(
            response.headers['HX-Redirect'],
            reverse('teachers:course_detail', args=[self.course.pk]),
        )

    def test_delete_without_htmx_redirects_to_history(self):
        session = self.make_session(days_from_today(-1))
        url = reverse('teachers:session_delete', args=[session.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('teachers:course_session_history', args=[self.course.pk]),
            fetch_redirect_response=False,
        )

    def test_other_teacher_cannot_delete_session(self):
        other_user = User.objects.create_user('profe2', password='pass')
        Teacher.objects.create(
            first_name='Luis', last_name='Martínez', user=other_user
        )
        self.client.force_login(other_user)
        session = self.make_session(days_from_today(-2))
        url = reverse('teachers:session_delete', args=[session.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(AttendanceSession.objects.filter(pk=session.pk).exists())


class CourseDetailViewTests(TestCase):
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

    def test_course_detail_has_no_post_handler(self):
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 405)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(-1)
            ).exists()
        )

    def test_today_card_rendered(self):
        url = reverse('teachers:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        self.assertContains(response, 'Sesión de hoy')
        self.assertContains(
            response,
            reverse('teachers:today_session_create', args=[self.course.pk]),
        )
        self.assertNotContains(response, 'Crear sesión en otra fecha')

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
        self.assertContains(response, 'Estudiante')
        self.assertContains(response, 'Asistencia')
        self.assertContains(response, '1/2 (50.0%)')
        self.assertContains(response, '0/2 (0.0%)')


class DashboardViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudentGroup.objects.create(name='Grupo Dash')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = User.objects.create_user('profe4', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Marta', last_name='López', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Música')
        cls.course = Course.objects.create(
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self):
        self.client.force_login(self.teacher_user)

    def test_dashboard_renders_quick_access_cards(self):
        url = reverse('teachers:dashboard')
        response = self.client.get(url)
        self.assertContains(response, 'Sesión de hoy')
        self.assertContains(response, 'Historial de sesiones')
        self.assertContains(
            response,
            reverse('teachers:today_session_create', args=[self.course.pk]),
        )
        self.assertContains(
            response,
            reverse('teachers:course_session_history', args=[self.course.pk]),
        )
