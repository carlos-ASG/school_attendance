from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from school.models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    NonSchoolDay,
    SchoolCycle,
    Student,
    StudentGroup,
    Subject,
    Teacher,
)
from school.services import create_attendance_records
from school.tests import add_full_week_schedule, make_cycle


def days_from_today(days: int) -> str:
    return (timezone.now().date() + timedelta(days=days)).isoformat()


class TodaySessionCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)

        cls.teacher_user = get_user_model().objects.create_user('profe1', password='pass')
        cls.other_user = get_user_model().objects.create_user('profe2', password='pass')

        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.other_teacher = Teacher.objects.create(
            first_name='Luis', last_name='Martínez', user=cls.other_user
        )

        cls.subject = Subject.objects.create(name='Ciencias')
        cls.cycle = make_cycle()
        cls.course = Course.objects.create(
            school_cycle=cls.cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )
        add_full_week_schedule(cls.course)

    def setUp(self) -> None:
        self.client.force_login(self.teacher_user)

    def test_create_today_session_redirects_to_today_detail(self):
        url = reverse('teacher_panel:today_session_create', args=[self.course.pk])
        response = self.client.post(url)
        session = AttendanceSession.objects.get(
            course=self.course, date=days_from_today(0)
        )
        self.assertRedirects(
            response,
            reverse('teacher_panel:today_session_detail', args=[session.pk]),
        )

    def test_create_today_session_generates_records(self):
        url = reverse('teacher_panel:today_session_create', args=[self.course.pk])
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
        url = reverse('teacher_panel:today_session_create', args=[self.course.pk])
        response = self.client.post(url)
        self.assertEqual(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(0)
            ).count(),
            1,
        )
        self.assertRedirects(
            response,
            reverse('teacher_panel:today_session_detail', args=[session.pk]),
        )

    def test_get_not_allowed(self):
        url = reverse('teacher_panel:today_session_create', args=[self.course.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_other_teacher_cannot_create_today_session(self):
        self.client.force_login(self.other_user)
        url = reverse('teacher_panel:today_session_create', args=[self.course.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(0)
            ).exists()
        )

    def test_today_non_school_day_rejected(self) -> None:
        NonSchoolDay.objects.create(
            cycle=self.cycle,
            name='Asueto de hoy',
            day_type=NonSchoolDay.DayType.ASUETO,
            start_date=days_from_today(0),
        )
        url = reverse('teacher_panel:today_session_create', args=[self.course.pk])
        response = self.client.post(url, follow=True)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(0)
            ).exists()
        )
        self.assertContains(response, 'inhábil')
        self.assertContains(response, 'Asueto de hoy')

    def test_today_out_of_cycle_rejected(self) -> None:
        past_cycle = make_cycle(
            'Ciclo Pasado',
            start=days_from_today(-200),
            end=days_from_today(-80),
        )
        self.course.school_cycle = past_cycle
        self.course.save(update_fields=['school_cycle'])
        url = reverse('teacher_panel:today_session_create', args=[self.course.pk])
        response = self.client.post(url, follow=True)
        self.assertFalse(
            AttendanceSession.objects.filter(course=self.course).exists()
        )
        self.assertContains(response, 'fuera del ciclo')

    def test_today_non_scheduled_weekday_rejected(self) -> None:
        today_weekday = timezone.now().date().weekday()
        self.course.schedule_slots.filter(weekday=today_weekday).delete()
        url = reverse('teacher_panel:today_session_create', args=[self.course.pk])
        response = self.client.post(url, follow=True)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(0)
            ).exists()
        )
        self.assertContains(response, 'no tiene clase')

    def test_today_course_without_schedule_rejected(self) -> None:
        self.course.schedule_slots.all().delete()
        url = reverse('teacher_panel:today_session_create', args=[self.course.pk])
        response = self.client.post(url, follow=True)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(0)
            ).exists()
        )
        self.assertContains(response, 'no tiene horario asignado')


class SessionUrlGuardTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = get_user_model().objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.cycle = make_cycle()
        cls.course = Course.objects.create(
            school_cycle=cls.cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self) -> None:
        self.client.force_login(self.teacher_user)

    def make_session(self, date: str) -> AttendanceSession:
        session = AttendanceSession.objects.create(
            course=self.course, date=date, created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def test_today_url_for_past_session_redirects(self):
        session = self.make_session(days_from_today(-1))
        url = reverse('teacher_panel:today_session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse('teacher_panel:session_detail', args=[session.pk]),
            fetch_redirect_response=False,
        )

    def test_previous_url_for_today_session_redirects(self):
        session = self.make_session(days_from_today(0))
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse('teacher_panel:today_session_detail', args=[session.pk]),
            fetch_redirect_response=False,
        )

    def test_other_teacher_cannot_open_session(self):
        other_user = get_user_model().objects.create_user('profe2', password='pass')
        Teacher.objects.create(
            first_name='Luis', last_name='Martínez', user=other_user
        )
        self.client.force_login(other_user)
        session = self.make_session(days_from_today(-1))
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class CourseSessionHistoryViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = get_user_model().objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.cycle = make_cycle()
        cls.course = Course.objects.create(
            school_cycle=cls.cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )
        add_full_week_schedule(cls.course)

    def setUp(self) -> None:
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
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.get(url)
        sessions = list(response.context['sessions'])
        self.assertIn(past_session, sessions)
        self.assertNotIn(today_session, sessions)

    def test_create_past_session_redirects_to_previous_page(self):
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        session = AttendanceSession.objects.get(
            course=self.course, date=days_from_today(-1)
        )
        self.assertRedirects(
            response, reverse('teacher_panel:session_detail', args=[session.pk])
        )
        self.assertEqual(session.records.count(), 1)

    def test_create_today_date_rejected(self):
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(0)})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(0)
            ).exists()
        )
        self.assertContains(response, 'Sesión de hoy')

    def test_create_future_session_rejected(self):
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
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
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(-1)
            ).count(),
            1,
        )

    def test_create_non_school_day_rejected(self) -> None:
        date = days_from_today(-2)
        NonSchoolDay.objects.create(
            cycle=self.cycle,
            name='Asueto histórico',
            day_type=NonSchoolDay.DayType.ASUETO,
            start_date=date,
        )
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': date})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AttendanceSession.objects.filter(course=self.course, date=date).exists()
        )
        self.assertContains(response, 'inhábil')
        self.assertContains(response, 'Asueto histórico')

    def test_create_out_of_cycle_date_rejected(self) -> None:
        date = (timezone.now().date() - timedelta(days=61)).isoformat()
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': date})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AttendanceSession.objects.filter(course=self.course, date=date).exists()
        )
        self.assertContains(response, 'fuera del ciclo')
        self.assertContains(response, str(self.cycle))

    def test_create_non_school_day_htmx_returns_form_fragment(self) -> None:
        date = days_from_today(-2)
        NonSchoolDay.objects.create(
            cycle=self.cycle,
            name='Asueto htmx',
            day_type=NonSchoolDay.DayType.ASUETO,
            start_date=date,
        )
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': date}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'inhábil')
        self.assertContains(response, 'Asueto htmx')
        self.assertIn('HX-Retarget', response.headers)
        self.assertEqual(response.headers['HX-Retarget'], '#session-form')

    def test_create_htmx_error_returns_form_fragment(self):
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(
            url, {'date': days_from_today(1)}, HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no puede ser posterior')
        self.assertIn('HX-Retarget', response.headers)
        self.assertEqual(response.headers['HX-Retarget'], '#session-form')

    def test_create_non_scheduled_weekday_rejected(self) -> None:
        date = timezone.now().date() - timedelta(days=2)
        self.course.schedule_slots.filter(weekday=date.weekday()).delete()
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': date.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AttendanceSession.objects.filter(course=self.course, date=date).exists()
        )
        self.assertContains(response, 'no tiene clase')

    def test_create_non_scheduled_weekday_htmx_returns_form_fragment(self) -> None:
        date = timezone.now().date() - timedelta(days=2)
        self.course.schedule_slots.filter(weekday=date.weekday()).delete()
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(
            url, {'date': date.isoformat()}, HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no tiene clase')
        self.assertIn('HX-Retarget', response.headers)
        self.assertEqual(response.headers['HX-Retarget'], '#session-form')

    def test_create_htmx_success_redirects_via_hx_redirect(self):
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
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
            reverse('teacher_panel:session_detail', args=[session.pk]),
        )

    def test_other_teacher_cannot_create_session(self):
        other_user = get_user_model().objects.create_user('profe2', password='pass')
        Teacher.objects.create(
            first_name='Luis', last_name='Martínez', user=other_user
        )
        self.client.force_login(other_user)
        url = reverse('teacher_panel:course_session_history', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(-1)
            ).exists()
        )


class PreviousSessionDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = get_user_model().objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.cycle = make_cycle()
        cls.course = Course.objects.create(
            school_cycle=cls.cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )
        cls.past_cycle = make_cycle(
            'Ciclo pasado',
            cycle_type=SchoolCycle.CycleType.QUATRIMESTRAL,
            start=days_from_today(-200),
            end=days_from_today(-110),
        )
        cls.past_course = Course.objects.create(
            school_cycle=cls.past_cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self) -> None:
        self.client.force_login(self.teacher_user)

    def make_session(self, date: str | None = None) -> AttendanceSession:
        session = AttendanceSession.objects.create(
            course=self.course, date=date or days_from_today(-1), created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def make_frozen_session(self) -> AttendanceSession:
        session = AttendanceSession.objects.create(
            course=self.past_course, date=days_from_today(-150), created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def formset_data(
        self, session: AttendanceSession, **overrides: str
    ) -> dict[str, str]:
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
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Presente')
        self.assertNotContains(response, '<select')

    def test_edit_mode_renders_batch_form(self):
        session = self.make_session()
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.get(url, {'edit': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="form-0-status"')
        self.assertContains(response, 'Guardar cambios')

    def test_batch_edit_saves_all_rows(self):
        session = self.make_session()
        record = session.records.first()
        url = reverse('teacher_panel:session_detail', args=[session.pk])
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
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.post(
            url,
            self.formset_data(session, **{'form-0-status': 'LATE'}),
            HTTP_HX_REQUEST='true',
        )
        self.assertContains(response, 'Cambios guardados')
        self.assertNotContains(response, '<select')

    def test_batch_edit_without_htmx_redirects_to_readonly(self):
        session = self.make_session()
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.post(
            url, self.formset_data(session, **{'form-0-status': 'EXCUSED'})
        )
        self.assertEqual(response.status_code, 302)

    def test_batch_edit_invalid_renders_form_with_errors(self):
        session = self.make_session()
        url = reverse('teacher_panel:session_detail', args=[session.pk])
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

    def test_frozen_session_stays_read_only_with_edit_flag(self):
        session = self.make_frozen_session()
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.get(url, {'edit': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<select')
        self.assertNotContains(response, 'name="form-0-status"')

    def test_frozen_session_shows_read_only_notice_and_hides_actions(self):
        session = self.make_frozen_session()
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sesión de solo lectura')
        self.assertContains(response, 'Entendido')
        self.assertNotContains(response, '?edit=1')
        self.assertNotContains(response, 'Eliminar sesión')

    def test_frozen_session_batch_edit_rejected_htmx(self):
        session = self.make_frozen_session()
        record = session.records.first()
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.post(
            url,
            self.formset_data(session, **{'form-0-status': 'ABSENT'}),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'solo lectura')
        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)

    def test_frozen_session_batch_edit_rejected_without_htmx(self):
        session = self.make_frozen_session()
        record = session.records.first()
        url = reverse('teacher_panel:session_detail', args=[session.pk])
        response = self.client.post(
            url, self.formset_data(session, **{'form-0-status': 'ABSENT'})
        )
        self.assertEqual(response.status_code, 302)
        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)


class TodaySessionDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = get_user_model().objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.cycle = make_cycle()
        cls.course = Course.objects.create(
            school_cycle=cls.cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )
    def setUp(self) -> None:
        self.client.force_login(self.teacher_user)

    def make_today_session(self) -> AttendanceSession:
        session = AttendanceSession.objects.create(
            course=self.course, date=days_from_today(0), created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def test_today_page_renders_editable(self):
        session = self.make_today_session()
        url = reverse('teacher_panel:today_session_detail', args=[session.pk])
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
        url = reverse('teacher_panel:today_session_detail', args=[session.pk])
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
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Test')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = get_user_model().objects.create_user('profe1', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Ana', last_name='García', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Ciencias')
        cls.cycle = make_cycle()
        cls.course = Course.objects.create(
            school_cycle=cls.cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )
        cls.past_cycle = make_cycle(
            'Ciclo pasado',
            cycle_type=SchoolCycle.CycleType.QUATRIMESTRAL,
            start=days_from_today(-200),
            end=days_from_today(-110),
        )
        cls.past_course = Course.objects.create(
            school_cycle=cls.past_cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self) -> None:
        self.client.force_login(self.teacher_user)

    def make_session(self, date: str) -> AttendanceSession:
        session = AttendanceSession.objects.create(
            course=self.course, date=date, created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def make_frozen_session(self) -> AttendanceSession:
        session = AttendanceSession.objects.create(
            course=self.past_course, date=days_from_today(-150), created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def test_delete_past_session_htmx_renders_list_fragment(self):
        session = self.make_session(days_from_today(-2))
        url = reverse('teacher_panel:session_delete', args=[session.pk])
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AttendanceSession.objects.filter(pk=session.pk).exists())
        self.assertFalse(
            AttendanceRecord.objects.filter(session_id=session.pk).exists()
        )
        self.assertContains(response, 'Aún no hay sesiones registradas.')

    def test_delete_last_session_shows_empty_state(self):
        session = self.make_session(days_from_today(-1))
        url = reverse('teacher_panel:session_delete', args=[session.pk])
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertContains(response, 'Aún no hay sesiones registradas.')

    def test_delete_today_session_htmx_redirects_to_course_detail(self):
        session = self.make_session(days_from_today(0))
        url = reverse('teacher_panel:session_delete', args=[session.pk])
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Redirect', response.headers)
        self.assertEqual(
            response.headers['HX-Redirect'],
            reverse('teacher_panel:course_detail', args=[self.course.pk]),
        )

    def test_delete_without_htmx_redirects_to_history(self):
        session = self.make_session(days_from_today(-1))
        url = reverse('teacher_panel:session_delete', args=[session.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('teacher_panel:course_session_history', args=[self.course.pk]),
            fetch_redirect_response=False,
        )

    def test_frozen_session_delete_htmx_is_rejected(self):
        session = self.make_frozen_session()
        url = reverse('teacher_panel:session_delete', args=[session.pk])
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AttendanceSession.objects.filter(pk=session.pk).exists())

    def test_frozen_session_delete_without_htmx_is_rejected(self):
        session = self.make_frozen_session()
        url = reverse('teacher_panel:session_delete', args=[session.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('teacher_panel:course_session_history', args=[self.past_course.pk]),
            fetch_redirect_response=False,
        )
        self.assertTrue(AttendanceSession.objects.filter(pk=session.pk).exists())

    def test_other_teacher_cannot_delete_session(self):
        other_user = get_user_model().objects.create_user('profe2', password='pass')
        Teacher.objects.create(
            first_name='Luis', last_name='Martínez', user=other_user
        )
        self.client.force_login(other_user)
        session = self.make_session(days_from_today(-2))
        url = reverse('teacher_panel:session_delete', args=[session.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(AttendanceSession.objects.filter(pk=session.pk).exists())


class CourseDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Asistencia')
        cls.student_a = Student.objects.create(
            first_name='Ana', paternal_surname='Pérez', maternal_surname='López'
        )
        cls.student_b = Student.objects.create(
            first_name='Beto', paternal_surname='García', maternal_surname='Ruiz'
        )
        cls.group.students.add(cls.student_a, cls.student_b)

        cls.teacher_user = get_user_model().objects.create_user('profe3', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Marta', last_name='López', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Historia')
        cls.cycle = make_cycle()
        cls.course = Course.objects.create(
            school_cycle=cls.cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )
        add_full_week_schedule(cls.course)

    def setUp(self) -> None:
        self.client.force_login(self.teacher_user)

    def make_session(self, date: str | None = None) -> AttendanceSession:
        session = AttendanceSession.objects.create(
            course=self.course, date=date or days_from_today(-1), created_by=self.teacher
        )
        create_attendance_records(session)
        return session

    def set_status(
        self, session: AttendanceSession, student: Student, status: str
    ) -> None:
        record = session.records.get(student=student)
        record.status = status
        record.save(update_fields=['status'])

    def test_course_detail_has_no_post_handler(self):
        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
        response = self.client.post(url, {'date': days_from_today(-1)})
        self.assertEqual(response.status_code, 405)
        self.assertFalse(
            AttendanceSession.objects.filter(
                course=self.course, date=days_from_today(-1)
            ).exists()
        )

    def test_today_card_rendered(self):
        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        self.assertContains(response, 'Tomar asistencia')
        self.assertContains(
            response,
            reverse('teacher_panel:today_session_create', args=[self.course.pk]),
        )
        self.assertNotContains(response, 'Crear sesión en otra fecha')

    def assert_today_card_disabled(self, response) -> None:
        self.assertRegex(
            response.content.decode(),
            r'(?s)<form method="post" action="[^"]*/sessions/today/">'
            r'.*?<button disabled\b[^>]*type="submit"',
        )

    def test_today_card_disabled_on_non_school_day(self) -> None:
        NonSchoolDay.objects.create(
            cycle=self.cycle,
            name='Asueto detalle',
            day_type=NonSchoolDay.DayType.ASUETO,
            start_date=days_from_today(0),
        )
        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assert_today_card_disabled(response)
        self.assertContains(response, 'Asueto detalle')

    def test_today_card_disabled_on_non_scheduled_weekday(self) -> None:
        today_weekday = timezone.now().date().weekday()
        self.course.schedule_slots.filter(weekday=today_weekday).delete()
        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assert_today_card_disabled(response)
        self.assertContains(response, 'no tiene clase')

    def test_today_card_disabled_without_schedule(self) -> None:
        self.course.schedule_slots.all().delete()
        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assert_today_card_disabled(response)
        self.assertContains(response, 'no tiene horario asignado')

    def test_history_link_works_for_other_cycle_course(self) -> None:
        past_cycle = make_cycle(
            'Ciclo Pasado Detalle',
            start=timezone.now().date() - timedelta(days=200),
            end=timezone.now().date() - timedelta(days=80),
        )
        self.course.school_cycle = past_cycle
        self.course.save(update_fields=['school_cycle'])
        session = self.make_session()
        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('teacher_panel:course_session_history', args=[self.course.pk]),
        )
        history = self.client.get(
            reverse('teacher_panel:course_session_history', args=[self.course.pk])
        )
        self.assertEqual(history.status_code, 200)
        self.assertIn(session, list(history.context['sessions']))

    def test_no_sessions_shows_zero_attendance(self):
        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
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

        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
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

        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        attendance = response.context['attendance']
        self.assertEqual(attendance[self.student_a.pk]['percentage'], '0.0')

    def test_other_course_records_not_counted(self):
        other_group = StudentGroup.objects.create(name='Grupo Otro')
        other_group.students.add(self.student_a)
        other_subject = Subject.objects.create(name='Geografía')
        other_course = Course.objects.create(
            student_group=other_group, teacher=self.teacher, subject=other_subject,
            school_cycle=self.cycle,
        )
        other_session = AttendanceSession.objects.create(
            course=other_course, date=days_from_today(-1), created_by=self.teacher
        )
        create_attendance_records(other_session)

        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
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

        url = reverse('teacher_panel:course_detail', args=[self.course.pk])
        response = self.client.get(url)
        self.assertContains(response, 'Estudiante')
        self.assertContains(response, 'Asistencia')
        self.assertContains(response, '1/2 (50.0%)')
        self.assertContains(response, '0/2 (0.0%)')


class DashboardViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.group = StudentGroup.objects.create(name='Grupo Dash')
        cls.student = Student.objects.create(
            first_name='Juan', paternal_surname='Pérez', maternal_surname='Gómez'
        )
        cls.group.students.add(cls.student)
        cls.teacher_user = get_user_model().objects.create_user('profe4', password='pass')
        cls.teacher = Teacher.objects.create(
            first_name='Marta', last_name='López', user=cls.teacher_user
        )
        cls.subject = Subject.objects.create(name='Música')
        cls.cycle = make_cycle()
        cls.course = Course.objects.create(
            school_cycle=cls.cycle,
            student_group=cls.group, teacher=cls.teacher, subject=cls.subject
        )

    def setUp(self) -> None:
        self.client.force_login(self.teacher_user)

    def test_dashboard_renders_ver_curso_button(self):
        url = reverse('teacher_panel:dashboard')
        response = self.client.get(url)
        self.assertContains(response, 'Ver curso')
        self.assertContains(
            response,
            reverse('teacher_panel:course_detail', args=[self.course.pk]),
        )
        self.assertNotContains(
            response,
            reverse('teacher_panel:today_session_create', args=[self.course.pk]),
        )

    def test_dashboard_lists_only_current_cycle_courses(self) -> None:
        past_cycle = make_cycle(
            'Ciclo Pasado', start=timezone.now().date() - timedelta(days=200),
            end=timezone.now().date() - timedelta(days=80),
        )
        past_subject = Subject.objects.create(name='Ed. Física')
        past_course = Course.objects.create(
            student_group=self.group, teacher=self.teacher,
            subject=past_subject, school_cycle=past_cycle,
        )
        url = reverse('teacher_panel:dashboard')
        response = self.client.get(url)
        courses = list(response.context['courses'])
        others = list(response.context['previous_cycle_courses'])
        self.assertIn(self.course, courses)
        self.assertNotIn(past_course, courses)
        self.assertIn(past_course, others)
        self.assertNotIn(self.course, others)

    def test_previous_cycle_courses_section_links_to_course_detail(self) -> None:
        past_cycle = make_cycle(
            'Ciclo Pasado Dash', start=timezone.now().date() - timedelta(days=200),
            end=timezone.now().date() - timedelta(days=80),
        )
        past_subject = Subject.objects.create(name='Ed. Física Dash')
        past_course = Course.objects.create(
            student_group=self.group, teacher=self.teacher,
            subject=past_subject, school_cycle=past_cycle,
        )
        url = reverse('teacher_panel:dashboard')
        response = self.client.get(url)
        self.assertContains(response, 'Ciclos anteriores')
        self.assertContains(response, 'Ciclo Pasado Dash')
        self.assertContains(
            response,
            reverse('teacher_panel:course_detail', args=[past_course.pk]),
        )
        self.assertNotContains(
            response,
            reverse('teacher_panel:today_session_create', args=[past_course.pk]),
        )

    def test_banner_on_non_school_day(self) -> None:
        NonSchoolDay.objects.create(
            cycle=self.cycle,
            name='Día de la Revolución',
            day_type=NonSchoolDay.DayType.ASUETO,
            start_date=days_from_today(0),
        )
        url = reverse('teacher_panel:dashboard')
        response = self.client.get(url)
        self.assertContains(response, 'Hoy no hay clases')
        self.assertContains(response, 'Día de la Revolución')

    def test_banner_when_no_cycle_in_progress(self) -> None:
        past_cycle = make_cycle(
            'Ciclo Pasado Banner', start=timezone.now().date() - timedelta(days=200),
            end=timezone.now().date() - timedelta(days=80),
        )
        self.course.school_cycle = past_cycle
        self.course.save(update_fields=['school_cycle'])
        self.cycle.delete()  # no cycle contains today anymore
        url = reverse('teacher_panel:dashboard')
        response = self.client.get(url)
        self.assertContains(response, 'No hay ciclo escolar en curso.')
        self.assertEqual(list(response.context['courses']), [])
        self.assertNotContains(response, 'Hoy no hay clases')

    def test_no_banner_on_normal_day(self) -> None:
        url = reverse('teacher_panel:dashboard')
        response = self.client.get(url)
        self.assertNotContains(response, 'Hoy no hay clases')
        self.assertNotContains(response, 'No hay ciclo escolar en curso.')
