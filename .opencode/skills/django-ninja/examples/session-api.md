# Example: Session-authenticated API for a server-rendered Django app

Pattern for an API consumed by the same site's frontend (cookies, not tokens):
Django session auth + CSRF, schemas grouped in the app, routers per domain.

```python
# src/school/api/attendance.py
from typing import List

from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.security import SessionAuth

from school.models import Session, Attendance

router = Router(auth=SessionAuth())          # CSRF enforced automatically


class AttendanceOut(Schema):
    student_id: int
    status: str
    note: str = None


class AttendanceUpdate(Schema):
    status: str
    note: str = None


@router.get("/sessions/{session_id}/attendance", response=List[AttendanceOut])
def list_attendance(request, session_id: int):
    return Attendance.objects.filter(session_id=session_id)


@router.post("/sessions/{session_id}/attendance", response={200: AttendanceOut, 404: None})
def mark(request, session_id: int, student_id: int, payload: AttendanceUpdate):
    session = get_object_or_404(Session, pk=session_id)
    obj, _ = Attendance.objects.update_or_create(
        session=session, student_id=student_id,
        defaults=payload.dict(exclude_unset=True),
    )
    return obj
```

```python
# src/school/api.py
from ninja import NinjaAPI
from ninja.security import django_auth

from school.api import attendance

api = NinjaAPI(
    title="School Attendance API",
    auth=django_auth,            # global default: any logged-in user
    urls_namespace="school-api",
)
api.add_router("/attendance/", attendance.router, tags=["Attendance"])


@api.get("/me", auth=None)       # public endpoint under global auth
def me(request):
    if not request.user.is_authenticated:
        return {"authenticated": False}
    return {"username": request.user.username, "authenticated": True}
```

```python
# src/config/urls.py
from school.api import api
urlpatterns = [path("api/", api.urls)]
```

Key points:

- Cookie-auth → CSRF auto-on; frontend requests need Django's CSRF token
  (AJAX pattern: https://docs.djangoproject.com/en/stable/howto/csrf/).
  For a token-based API instead, use `HttpBearer` and keep `csrf=OFF`.
- `auth=None` opts single endpoints out of global session auth.
- `request.auth` is the authenticated `User` after `django_auth`.
- Narrower access per route: `SessionAuthIsStaff()` / `SessionAuthSuperUser()`.
- Since this repo has no API yet, `uv add django-ninja` first and add
  `path("api/", api.urls)` to `src/config/urls.py`.
