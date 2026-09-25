from typing import Any

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from school.models import AttendanceSession
from school.models import Teacher
from school.selectors import get_teacher as get_teacher_for_user


def get_teacher(request: HttpRequest) -> Teacher | None:
    """Return the Teacher linked to the request user, or None."""
    if request.user.is_authenticated:
        return get_teacher_for_user(user=request.user)
    return None


def session_detail_url(session: AttendanceSession) -> str:
    """Return the detail URL for a session based on its date (D1)."""
    if session.date == timezone.now().date():
        return reverse("teacher_panel:today_session_detail", args=[session.pk])
    return reverse("teacher_panel:session_detail", args=[session.pk])


class TeacherRequiredMixin:
    """Allow access only to authenticated users linked to a Teacher."""

    teacher: Teacher

    def dispatch(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        teacher = get_teacher(request)
        if teacher is None:
            raise PermissionDenied
        self.teacher = teacher
        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]
