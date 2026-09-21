import hmac

from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import APIKeyHeader, SessionAuth

from integrations.keys import KEY_PREFIX_LENGTH, hash_key
from integrations.models import DesktopApiKey
from school.models import Teacher
from teacher_panel.views.mixins import get_teacher


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


class DesktopApiKeyAuth(APIKeyHeader):
    """API key de escritorio por header X-API-Key.

    Lookup por prefijo + comparación timing-safe del hash + verificación de
    no revocada. Todo fallo (header ausente, key inexistente o revocada)
    produce el mismo 401 genérico, sin distinguir el motivo.
    """

    param_name = 'X-API-Key'

    def authenticate(
        self, request: HttpRequest, key: str | None
    ) -> DesktopApiKey | None:
        if not key:
            return None
        candidate = DesktopApiKey.objects.filter(
            prefix=key[:KEY_PREFIX_LENGTH]
        ).first()
        if candidate is None:
            return None
        if not hmac.compare_digest(candidate.hash, hash_key(key)):
            return None
        if candidate.revoked_at is not None:
            return None
        return candidate
