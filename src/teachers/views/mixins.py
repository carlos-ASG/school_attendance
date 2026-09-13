from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy

from school.models import Teacher


def get_teacher(request):
    """Return the Teacher linked to the request user, or None."""
    if request.user.is_authenticated:
        return Teacher.objects.filter(user=request.user).first()
    return None


class TeacherRequiredMixin:
    """Allow access only to authenticated users linked to a Teacher."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse_lazy('teachers:login'))
        self.teacher = get_teacher(request)
        if self.teacher is None:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
