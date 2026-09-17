from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import SessionAuth

from school.models import Teacher
from teachers.views.mixins import get_teacher


class TeacherSessionAuth(SessionAuth):
    """Session-cookie auth (CSRF enforced by the cookie-auth base class)
    restricted to users linked to a Teacher.

    Unauthenticated → 401, authenticated without a linked Teacher → 403.
    On success the Teacher instance is stored in request.auth.
    """

    def authenticate(self, request: HttpRequest, token: str | None) -> Teacher | None:
        if not request.user.is_authenticated:
            return None
        teacher = get_teacher(request)
        if teacher is None:
            raise HttpError(403, 'No autorizado: el usuario no está vinculado a un profesor.')
        return teacher
