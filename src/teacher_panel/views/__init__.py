from .auth import HomeRedirectView
from .course_detail import CourseDetailView
from .course_session_history import CourseSessionHistoryView, SessionDeleteView
from .dashboard import DashboardView
from .mixins import TeacherRequiredMixin, get_teacher, session_detail_url
from .session_detail import PreviousSessionDetailView
from .student_detail import StudentDetailView
from .today_session import (
    TodaySessionCreateView,
    TodaySessionDetailView,
)

__all__ = [
    'HomeRedirectView',
    'DashboardView',
    'CourseDetailView',
    'CourseSessionHistoryView',
    'TodaySessionCreateView',
    'TodaySessionDetailView',
    'PreviousSessionDetailView',
    'StudentDetailView',
    'SessionDeleteView',
    'TeacherRequiredMixin',
    'get_teacher',
    'session_detail_url',
]
