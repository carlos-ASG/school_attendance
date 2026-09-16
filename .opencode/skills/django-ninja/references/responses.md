# Responses

## Declaring response schemas

Optional but recommended: validates output, enables docs, converts Django
objects/querysets automatically.

```python
from typing import List
from ninja import Schema

class UserSchema(Schema):
    username: str
    is_authenticated: bool
    email: str = None          # defaults make fields optional

@api.get("/me", response=UserSchema)
def me(request):
    return request.user        # ORM object auto-serialized

@api.get("/employees", response=List[EmployeeOut])
def list_employees(request):
    return Employee.objects.all()   # queryset auto-evaluated and converted
```

## Multiple response types

Map status → schema; return `(status, data)` tuples to pick one:

```python
class Error(Schema):
    message: str

@api.get("/me", response={200: UserSchema, 403: Error})
def me(request):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    return request.user
```

Without a declared `response`, returning a dict/list/scalar serializes as-is
(no validation).

## Altering the response

Inject extra headers/status on an otherwise normal return:

```python
from ninja import NinjaAPI
from ninja.response import Response  # only for direct HttpResponse building

@api.get("/download")
def download(request, response: HttpResponse):   # magic name "response" = injector
    response.set_cookie("download", "started")
    return {"file": "report.pdf"}
```

The parameter must be exactly named `response` and typed `HttpResponse` —
ninja passes its internal response object for you to mutate. Use
`api.create_response(request, data, status=...)` when building raw responses
manually (e.g. in exception handlers).

## Pagination

Built-in classes from `ninja.pagination`:

```python
from ninja.pagination import paginate, PageNumberPagination, LimitOffsetPagination

@api.get("/books", response=List[BookOut])
@paginate(PageNumberPagination, page_size=20)   # decorator BELOW @api
def list_books(request, **kwargs):
    return Book.objects.all()
```

- `@paginate` must sit under the `@api.get(...)` decorator, above the function.
- Response wraps results plus `count`, `page_size`, `links` etc.
- `LimitOffsetPagination` for `limit`/`offset` params; custom pagination by
  subclassing and overriding `paginate_queryset`.

## Renderers / non-JSON

JSON is default. Custom renderers (e.g. CSV) via
`response_class` / renderers — see
https://django-ninja.dev/guides/response/response-renderers/
