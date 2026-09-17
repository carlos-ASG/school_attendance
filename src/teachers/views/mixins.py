from typing import Any

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils import timezone

from school.models import AttendanceSession, Teacher


def get_teacher(request: HttpRequest) -> Teacher | None:
    """Return the Teacher linked to the request user, or None."""
    if request.user.is_authenticated:
        return Teacher.objects.filter(user=request.user).first()
    return None


def session_detail_url(session: AttendanceSession) -> str:
    """Return the detail URL for a session based on its date (D1)."""
    if session.date == timezone.now().date():
        return reverse('teachers:today_session_detail', args=[session.pk])
    return reverse('teachers:session_detail', args=[session.pk])


class TeacherRequiredMixin:
    """Allow access only to authenticated users linked to a Teacher."""

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        self.teacher = get_teacher(request)
        if self.teacher is None:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
