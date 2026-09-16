# Input: Path, Query, Body, Form, Files

Order doesn't matter in the signature — resolution is by name/type:

1. Parameter name matches a path `{placeholder}` → **path** param.
2. `Path[Schema]` → path params grouped into a schema.
3. `Form[...]` → form data.
4. `Query[Schema]` → query params grouped into a schema.
5. `Schema`/`BaseModel` type → JSON **body**.
6. Any other annotation (`int`, `str`, `date`, `bool`, `List[int]`, …) →
   **query** param. Unannotated → `str`.

## Path parameters

```python
@api.get("/items/{item_id}")
def read_item(request, item_id: int):        # validated, 422 if not an int
    return {"item_id": item_id}

@api.get("/events/{year}/{month}/{day}")
def events(request, year: int, month: int, day: int): ...
```

Django path converters work too (`{int:item_id}`, `{slug:…}`, `{path:value}` —
with `{path:value}` the segment may contain slashes). With converters the value
is still `str` unless you annotate.

Group related path params into a schema with the `Path` hint:

```python
from ninja import Schema, Path

class PathDate(Schema):
    year: int
    month: int
    day: int

    def value(self):  # add helper methods freely
        import datetime
        return datetime.date(self.year, self.month, self.day)

@api.get("/events/{year}/{month}/{day}")
def events(request, date: Path[PathDate]):
    return {"date": date.value()}
```

## Query parameters

```python
@api.get("/weapons")
def list_weapons(request, limit: int = 10, offset: int = 0): ...
# /weapons?offset=0&limit=10
```

- Defaults make params optional; no default → required (422 if missing).
- `bool` accepts `1/true/on/yes` (any case) as `True`.
- `date` accepts ISO strings or unix timestamps.

Schema for multiple query params (`Query` hint required to avoid body routing):

```python
from ninja import Query, Schema
from pydantic import Field

class Filters(Schema):
    limit: int = 100
    offset: int = None
    query: str = None
    category__in: list[str] = Field(None, alias="categories")  # ?categories=a&categories=b

@api.get("/filter")
def events(request, filters: Query[Filters]):
    return {"filters": filters.dict()}
```

## Request body (JSON)

```python
from ninja import Schema

class Item(Schema):
    name: str
    description: str = None     # optional field
    price: float
    quantity: int

@api.post("/items")
def create(request, item: Item):
    return item

@api.put("/items/{item_id}")                       # body + path together
def update(request, item_id: int, item: Item): ...

@api.post("/items/{item_id}")                      # body + path + query together
def update2(request, item_id: int, item: Item, q: str): ...
```

`item.dict()` / `item.dict(exclude_unset=True)` convert to plain dicts for
model kwargs.

## Form data

```python
from ninja import Form, Schema

@api.post("/login")
def login(request, username: Form[str], password: Form[str]): ...

class Item(Schema):
    name: str
    description: str = None

@api.post("/items")
def create(request, item: Form[Item]):          # Form[Schema] = multipart/urlencoded
    return item
```

Form + path + query can be mixed like body + path + query.

Optional form fields sent as empty strings fail `int`/`bool` validation; fix
with a `WrapValidator` that maps `""` to the default (see
https://django-ninja.dev/guides/input/form-params/).

## File uploads

```python
from ninja import UploadedFile, File
from django.core.files.storage import FileSystemStorage

STORAGE = FileSystemStorage()

@api.post("/upload")
def upload(request, cv: File[UploadedFile]):
    filename = STORAGE.save(cv.name, cv)

@api.post("/employees")          # files combine with body schema
def create_employee(request, payload: EmployeeIn, cv: File[UploadedFile]):
    employee = Employee(**payload.dict())
    employee.cv.save(cv.name, cv)
    return {"id": employee.id}
```

`UploadedFile` is Django's `UploadedFile`; use `List[File[UploadedFile]]` for
multi-file fields.

## Validation errors

Invalid input returns HTTP 422:

```json
{"detail": [{"loc": ["query", "name"], "msg": "field required", "type": "value_error.missing"}]}
```

`loc` first element names the source: `path`, `query`, `body`, `form`.
