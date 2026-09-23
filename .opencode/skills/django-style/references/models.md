# Models: constraints, clean, properties/methods

Models own the data model — structure, integrity, and simple derived values.
Everything that spans relations or orchestrates belongs in
`selectors.py` / `services.py` instead.

## BaseModel

Give every app a `BaseModel` (or reuse a shared one) with the audit stamps:

```python
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

## Validation: constraints first

If the database can enforce it, let it. Constraints hold no matter who
writes — the ORM, a data migration, raw SQL, another service.

```python
from django.db.models import Q, F


class OrderLine(models.Model):
    orderid = models.CharField(max_length=255)
    sku = models.CharField(max_length=255)
    qty = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["orderid", "sku"],
                name="unique_orderline_per_order",
            ),
            models.CheckConstraint(
                name="qty_positive",
                check=Q(qty__gt=0),
            ),
        ]
```

Since Django >= 4.1, `full_clean()` also validates `Meta.constraints` and
raises a friendly `ValidationError`. Going through
`Model.objects.create(...)` directly still surfaces `IntegrityError` — so
services call `full_clean()` before `save()` (see `references/services.md`).

## Validation: `clean` / `full_clean`

`clean()` is for **simple** validation across **non-relational fields**:

```python
from django.core.exceptions import ValidationError


class Course(BaseModel):
    name = models.CharField(unique=True, max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("End date cannot be before start date")
```

Nobody calls `clean()` automatically — the service does it via
`obj.full_clean()` right before `obj.save()`. This also matches Django
admin/forms behavior, which run `full_clean` for free.

Move validation to the service when it is complex or must fetch related
data / span relations. Having both is fine; prefer the service when in
doubt.

## Properties

Simple derived value, non-relational fields, cheap to compute:

```python
from django.utils import timezone


class Course(BaseModel):
    ...
    @property
    def has_started(self) -> bool:
        return self.start_date <= timezone.now().date()

    @property
    def has_finished(self) -> bool:
        return self.end_date <= timezone.now().date()
```

Promote to a selector when it spans relations or risks N+1 (e.g.
`allocated_quantity` summing `self.allocations.all()` — fine on a single
instance, disastrous in a serialized list; the selector annotates
`Coalesce(Sum(...), 0)` in SQL instead).

## Methods

Same rules as properties, but with arguments — or for paired attribute
setting:

```python
class Token(BaseModel):
    secret = models.CharField(max_length=255, unique=True)
    expiry = models.DateTimeField(blank=True, null=True)

    def set_new_secret(self):
        self.secret = get_random_string(255)
        self.expiry = timezone.now() + settings.TOKEN_EXPIRY_TIMEDELTA
        return self
```

Setting `secret` without updating `expiry` is a bug; the method makes the
pair atomic at the instance level.

## Decision table

| Need                                              | Put it in            |
| ------------------------------------------------- | -------------------- |
| Integrity rule expressible as a constraint        | `Meta.constraints`   |
| Simple validation, non-relational fields          | `clean()`            |
| Complex / relation-spanning validation            | Service              |
| Simple derived value, no relations                | `@property`          |
| Simple derived value with arguments               | Model method         |
| Derived value spanning relations / N+1 risk       | Selector (annotate)  |
| Any write or cross-model orchestration            | Service              |

## Testing models

Only test models that have something extra (validation, properties,
methods). No database needed when only calling `full_clean`:

```python
class CourseTests(TestCase):
    def test_course_end_date_cannot_be_before_start_date(self):
        course = Course(
            name="T",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            course.full_clean()
```
