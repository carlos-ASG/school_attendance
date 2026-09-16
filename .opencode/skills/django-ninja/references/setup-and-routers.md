# Setup, URLs, and Routers

## NinjaAPI constructor options

```python
from ninja import NinjaAPI

api = NinjaAPI(
    csrf=False,           # set ON to enforce Django CSRF on all operations
    auth=None,            # global authenticator (see auth-and-csrf.md)
    version="1.0.0",      # OpenAPI version fields
    title="Demo API",
    docs_url="/docs",     # Swagger UI (None disables)
    openapi_url="/openapi.json",
    urls_namespace="demo-api",  # unique per API when mounting several
)
```

Optional: add `"ninja"` to `INSTALLED_APPS` so Swagger/Redoc load their JS
bundle locally instead of from a CDN.

## Wiring into urls.py

```python
# src/config/urls.py
from django.urls import path
from school.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
```

Auto docs then live at `/api/docs` (Swagger UI) and `/api/docs/redoc`
(Redoc). Docs UI is only enabled when `DEBUG=True` by default.

## Multiple APIs on one project

Each `NinjaAPI()` gets its own namespace; override explicitly when mounting
more than one:

```python
api2 = NinjaAPI(urls_namespace="payments-api")
```

## Routers

Keep operations domain-scoped instead of one giant `api.py`:

```python
# src/school/api/events.py
from ninja import Router

router = Router()

@router.get("/events")
def list_events(request): ...
```

```python
# src/school/api.py
from ninja import NinjaAPI
from school.api import events, attendance

api = NinjaAPI()
api.add_router("/events/", events.router)
api.add_router("/attendance/", attendance.router, tags=["Attendance"])
```

Router-level options (override API-level, applied to all its operations):
`auth`, `tags`. `add_router` path prefix + router's own paths are joined.

Reverse resolution: `api.urls` supports `reverse("demo-api:list_events")` with
router operation ids — see https://django-ninja.dev/guides/urls/

## Decorators on operations

Standard Django decorators stack fine (ninja outermost):

```python
@api.get("/report")
@cache_page(60)
def report(request): ...
```

`@api.operation(methods=[...], path=...)` exists as a lower-level alias for
`api_operation` / method decorators.
