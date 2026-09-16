# Schemas: Schema, ModelSchema, PatchDict, FilterSchema

`ninja.Schema` is Pydantic `BaseModel` (renamed to avoid clashing with Django
models). Everything Pydantic v2 works: validators, `Field`, `ConfigDict`,
aliases, nested models.

## Plain Schema (input or output)

```python
from datetime import date
from ninja import Schema

class EmployeeIn(Schema):
    first_name: str
    last_name: str
    department_id: int = None
    birthdate: date = None
```

Strict field validation (reject unknown keys instead of ignoring them):

```python
from pydantic import ConfigDict

class EmployeeIn(Schema):
    model_config = ConfigDict(extra="forbid")
    ...
```

## ModelSchema (schema generated from a Django model)

```python
from ninja import ModelSchema

class EmployeeOut(ModelSchema):
    class Meta:
        model = Employee
        fields = ["id", "first_name", "last_name", "department_id", "birthdate"]
        # or fields = "__all__"  (discouraged — data-exposure risk)
        # or exclude = ["password"]
        # fields_optional = "__all__" | ["description"]  (make some/all optional)
```

- `model` can be a string reference (`"auth.User"`).
- Override/extend by declaring annotated attributes:

```python
class GroupSchema(ModelSchema):
    class Meta:
        model = Group
        fields = ["id", "name"]

class UserSchema(ModelSchema):
    groups: List[GroupSchema] = []          # new/nested field
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]
```

Custom Django field types: register a mapping once via
`from ninja.orm import register_field; register_field("VectorField", list[float])`.

Schemas update in sync with the model but require the model resolved at import
time (fine for normal apps).

## Partial updates (PATCH)

Option A — make fields optional on a `ModelSchema`:

```python
class PatchGroupSchema(ModelSchema):
    class Meta:
        model = Group
        fields = ["id", "name", "description"]
        fields_optional = "__all__"

@api.patch("/patch/{pk}")
def patch(request, pk: int, payload: PatchGroupSchema):
    obj = MyModel.objects.get(pk=pk)
    for attr, value in payload.dict(exclude_unset=True).items():  # exclude_unset!
        setattr(obj, attr, value)
    obj.save()
```

Option B — `PatchDict` makes every field optional automatically and yields a
dict of only the provided keys:

```python
from ninja import PatchDict

class GroupSchema(Schema):
    name: str
    description: str
    due_date: date

@api.patch("/patch/{pk}")
def modify_data(request, pk: int, payload: PatchDict[GroupSchema]):
    obj = MyModel.objects.get(pk=pk)
    for attr, value in payload.items():     # only fields present in request
        setattr(obj, attr, value)
    obj.save()
```

## FilterSchema (queryset filtering from query params)

```python
from ninja import FilterSchema, FilterLookup, FilterConfigDict
from typing import Annotated, Optional
from datetime import datetime

class BookFilterSchema(FilterSchema):
    name: Annotated[Optional[str], FilterLookup("name__icontains")] = None
    search: Annotated[Optional[str], FilterLookup(
        ["name__icontains", "author__name__icontains", "publisher__name__icontains"]
    )] = None
    popular: Optional[bool] = None

    model_config = FilterConfigDict(expression_connector="AND")  # or "OR"/"XOR"

    def filter_popular(self, value: bool) -> Q:   # custom per-field logic wins
        return Q(view_count__gt=1000) | Q(download_count__gt=100) if value else Q()
```

Use with `Query` and one-line apply:

```python
@api.get("/books")
def list_books(request, filters: Query[BookFilterSchema]):
    books = Book.objects.all()
    books = filters.filter(books)
    return books
```

Behavior: `None` values are skipped; each non-None field becomes a `Q`;
fields join with `model_config` connector (default `AND`); multiple lookups in
one field join with `OR` by default (override with
`FilterLookup(..., expression_connector="AND")`). `FilterLookup('__icontains')`
as a generic alias appends the suffix to the field name. Force filtering on
`None` with `FilterLookup(..., ignore_none=False)`. Full custom logic:
`def custom_expression(self) -> Q`.

Deprecated: `Field(None, q="name__icontains")` — still works, but prefer
`Annotated[..., FilterLookup(...)]` (IDE-friendly, no Pydantic extra-args).

## Related docs

- Dynamic schema generation: https://django-ninja.dev/guides/response/django-pydantic-create-schema/
- Overriding Pydantic config per schema: https://django-ninja.dev/guides/response/config-pydantic/
