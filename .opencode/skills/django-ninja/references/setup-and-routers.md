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

## One docs page with a spec selector (per-auth or per-group docs)

Swagger UI's Topbar plugin renders a dropdown when configured with `urls`
(an array of `{url, name}`) + `urls.primaryName` — see
https://django-ninja.dev/guides/api-docs/ ("Creating custom docs viewer") and
https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
(`urls`, `urls.primaryName`). Use this to show separate docs pages (e.g. one
for API-key endpoints, one for session endpoints) from a single `NinjaAPI`
and a single URL, without splitting routers or mounts:

1. Disable the built-in docs page (keeps `/api/openapi.json` serving the full
   schema):

   ```python
   api = NinjaAPI(title="Demo API", docs_url=None)
   ```

2. Subclass `Swagger` and feed the selector config through the settings —
   ninja's `swagger-ui-init.js` passes `swagger-settings` JSON verbatim to
   `SwaggerUIBundle(...)`. **Caveat: ninja's bundle does NOT ship the Topbar
   plugin** (`SwaggerUIBundle.SwaggerUIStandalonePreset` is `undefined`), and
   with `urls` and no Topbar nothing loads → blank page. Vendor the
   matching `swagger-ui-standalone-preset.js` (same version as the bundled
   core, e.g. `https://unpkg.com/swagger-ui@3.40.0/dist/swagger-ui-standalone-preset.js`
   for ninja's 3.40.0) into your static files, extend the template, and use
   `layout: "StandaloneLayout"`:

   ```python
   # src/<app>/docs.py
   import json
   from django.http import HttpResponse
   from django.urls import reverse
   from ninja.openapi.docs import Swagger, render_template

   SPECS = {
       "desktop": {  # endpoints requiring API key
           "name": "Integrations (X-API-Key)",
           "title": "Integrations API",
           "include": lambda p: p.startswith("/api/desktop/"),
       },
       "session": {
           "name": "Teacher panel (session)",
           "title": "Teacher API",
           "include": lambda p: not p.startswith("/api/desktop/"),
       },
   }

   def filtered_schema(spec: str) -> dict:
       d = SPECS[spec]
       schema = dict(api.get_openapi_schema())
       schema["paths"] = {p: ops for p, ops in schema["paths"].items() if d["include"](p)}
       schema["info"] = {**schema["info"], "title": d["title"]}
       return schema

   class MultiSpecSwagger(Swagger):
       template = "app/swagger_multispec.html"  # copy of ninja/swagger.html
       # + <script src="{% static 'app/swagger-ui-standalone-preset.js' %}">
       #   then AFTER swagger-ui-bundle.js and BEFORE swagger-ui-init.js:
       #   <script>window.SwaggerUIBundle.SwaggerUIStandalonePreset =
       #     window.SwaggerUIStandalonePreset;</script>
       #   (the dist file defines the window global; ninja's init.js reads it
       #    off SwaggerUIBundle)

       def render_page(self, request, api, **kwargs) -> HttpResponse:
           settings = {**self.settings}  # never mutate self.settings in place
           settings["layout"] = "StandaloneLayout"
           settings["urls"] = [
               {"url": reverse("app-docs:schema", args=[slug]), "name": d["name"]}
               for slug, d in SPECS.items()
           ]
           settings["urls.primaryName"] = SPECS["session"]["name"]  # default page
           context = {
               "swagger_settings": json.dumps(settings, indent=1),
               "api": api,
               "add_csrf": any(getattr(a, "csrf", False) for a in api.auth),
           }
           return render_template(request, self.template, self.template_cdn, context)
   ```

3. Serve one page + one JSON per spec (small `urls.py` with `app_name` so
   `reverse()` works), and wire it alongside `api.urls`:

   ```python
   # src/config/urls.py — /api/docs is the single docs URL
   path("api/", include("app.urls")),  # docs page + <slug>.json views
   path("api/", api.urls),
   ```

   JSON views: `JsonResponse(filtered_schema(spec))` with an `Http404` guard
   for unknown slugs.

Notes:
- Filter on full schema path keys (`/api/desktop/...`) — `get_openapi_schema()`
  returns absolute paths with an empty `servers` list when mounted via `path("api/", ...)`.
- Keep `add_csrf` so "Try it out" sends `X-CSRFToken` for cookie-auth endpoints.
- Each filtered JSON keeps all `components.securitySchemes`, so the desktop
  page still shows the Authorize button for `X-API-Key`.

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
