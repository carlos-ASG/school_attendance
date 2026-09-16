---
name: django-ninja
description: Use when building JSON APIs with django-ninja (NinjaAPI, api.py, @api.get/post/put/patch/delete, Schema/ModelSchema, Query/Form/File hints, routers, auth=, CSRF) — or when the user mentions django-ninja, ninja, NinjaAPI, or wants a typed REST/OpenAPI layer in a Django app.
license: MIT
---

# Django Ninja

Django Ninja is a FastAPI-like framework for Django: you declare operations
(`@api.get(...)`) and Pydantic-based `Schema` classes; it parses/validates input,
renders responses, and auto-generates OpenAPI docs at `/api/docs`. Official
docs: https://django-ninja.dev

Run everything via `uv run manage.py <cmd>`. Install with `uv add django-ninja`
(adding `ninja` to `INSTALLED_APPS` is optional — it just bundles the Swagger JS
instead of loading it from a CDN).

## Quick start

```python
# src/<app>/api.py
from ninja import NinjaAPI, Schema

api = NinjaAPI()

class HelloSchema(Schema):
    name: str = "world"

@api.get("/hello")
def hello(request, name: str = "world"):
    return f"Hello {name}"

@api.post("/hello")
def hello_post(request, data: HelloSchema):
    return f"Hello {data.name}"
```

```python
# src/config/urls.py
from django.urls import path
from school.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
```

## How parameters are resolved (the core mental model)

Function signature alone determines where each argument comes from:

| Function parameter                            | Source                          |
| --------------------------------------------- | ------------------------------- |
| Matches a `{placeholder}` in the path         | Path                            |
| Singular type (`int`, `str`, `date`, `bool`…) | Query string                    |
| `Schema` subclass (or `BaseModel`)            | JSON request body               |
| `Form[str]` / `Form[SomeSchema]`              | Form data (`request.POST`)      |
| `Query[SomeSchema]`                           | Query string, grouped as schema |
| `File[UploadedFile]`                          | Uploaded file                   |
| `Path[SomeSchema]`                            | Path, grouped as schema         |
| Named `payload: SomeSchema` etc.              | Body (any name works)           |

First parameter is always the Django `request`. Unannotated params are `str`.
Missing required input → HTTP 422 with a `detail` list (`loc`, `msg`, `type`).

## Operations

`@api.get`, `@api.post`, `@api.put`, `@api.patch`, `@api.delete` cover the
standard methods. For multi-method or extra methods:

```python
@api.api_operation(["POST", "PATCH"], "/path")   # also HEAD/OPTIONS
def mixed(request): ...
```

## Responses

- Return anything JSON-serializable, a model instance, or a queryset directly.
- Declare `response=SomeSchema` (or `List[SomeSchema]`, or
  `{200: OkSchema, 403: ErrSchema}`) for validation + docs; returning ORM
  objects/querysets then auto-converts.
- Tuple return `(status, data)` selects which declared response to use:
  `return 403, {"message": "Please sign in first"}`.

## Workflow

1. Read the reference matching the task (see table below) before writing code.
2. Split large APIs with routers (`api.add_router(...)`), one `Router` per
   domain — see `references/setup-and-routers.md`.
3. Verify: `uv run manage.py check`, then hit `/api/docs` (or runserver +
   curl) for the new operations.

## Detailed references

| Topic                                                          | File                            |
| -------------------------------------------------------------- | ------------------------------- |
| NinjaAPI setup, urls wiring, routers, versioning, docs           | `references/setup-and-routers.md` |
| Path / query / body / form / file input, `Query[...]` schemas   | `references/input-params.md`    |
| `Schema` vs `ModelSchema`, optional fields, `PatchDict`, `FilterSchema` | `references/schemas.md`  |
| Response schemas, multi-status responses, pagination            | `references/responses.md`       |
| Authentication classes, CSRF behavior                           | `references/auth-and-csrf.md`   |

## Examples

| Example                                          | File                |
| ------------------------------------------------ | ------------------- |
| Full CRUD against a Django model (in/out schemas) | `examples/crud.md`  |
| Session-authenticated API + serializer pattern    | `examples/session-api.md` |

## Gotchas

- **CSRF is OFF by default** for all operations; it auto-enables only for
  cookie-based auth (`django_auth`, `APIKeyCookie`). Explicitly enable with
  `NinjaAPI(csrf=ON)` when the API must accept session-cookie requests.
  See `references/auth-and-csrf.md`.
- **PATCH**: pass `payload.dict(exclude_unset=True)` — plain `.dict()`
  overwrites every field with `None`. `PatchDict[Schema]` does this for you.
- **Strict input**: unknown body fields are silently ignored; use
  `model_config = ConfigDict(extra="forbid")` to reject them.
- **`fields = "__all__"`** on `ModelSchema` is discouraged (accidental data
  exposure, e.g. password hashes); always list fields explicitly or `exclude`.
- Deprecated: `Field(q=...)` on `FilterSchema` — use `FilterLookup`
  annotations instead (see `references/schemas.md`).
- Auth failures raise 401 before your handler runs; the authenticator's
  return value lands in `request.auth`.
