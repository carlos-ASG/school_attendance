# Example: allocation flow (models → selector → service → API)

A complete inventory-allocation use case showing every layer working
together. Adapt names to the app's domain (`src/<app>/`).

## 1. `models.py` — structure + integrity + instance-level rules

```python
from django.db import models


class Batch(models.Model):
    reference = models.CharField(max_length=255, unique=True)
    sku = models.CharField(max_length=255, db_index=True)
    purchased_quantity = models.PositiveIntegerField()
    eta = models.DateField(null=True, blank=True)  # None = in stock

    class Meta:
        ordering = ["eta"]

    def __str__(self) -> str:
        return f"Batch {self.reference} ({self.sku})"

    @property
    def allocated_quantity(self) -> int:
        # Instance-level, on-demand — fine for a single batch.
        # In lists, use the selector's annotation instead (N+1).
        return sum(line.qty for line in self.allocations.all())

    @property
    def available_quantity(self) -> int:
        return self.purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: "OrderLine") -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty


class OrderLine(models.Model):
    orderid = models.CharField(max_length=255)
    sku = models.CharField(max_length=255)
    qty = models.PositiveIntegerField()
    batch = models.ForeignKey(
        Batch,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="allocations",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["orderid", "sku"],
                name="unique_orderline_per_order",
            )
        ]
```

## 2. `selectors.py` — reads with SQL-side aggregation

```python
from typing import Optional
from django.db.models import QuerySet, F, Sum, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce

from .models import Batch


def batch_get_by_reference(*, reference: str) -> Optional[Batch]:
    """Fetch a Batch by reference, allocations prefetched."""
    return (
        Batch.objects.filter(reference=reference)
        .prefetch_related("allocations")
        .first()
    )


def batch_list_available_for_allocation(*, sku: str) -> QuerySet[Batch]:
    """
    Batches with stock for a SKU, by business priority:
    1. In-stock batches first (eta=None).
    2. In-transit batches by earliest eta.
    """
    return (
        Batch.objects.filter(sku=sku)
        .annotate(
            total_allocated=Coalesce(Sum("allocations__qty"), 0),
            available_qty=F("purchased_quantity") - F("total_allocated"),
        )
        .filter(available_qty__gt=0)
        .order_by(
            Case(
                When(eta__isnull=True, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            "eta",
        )
    )
```

## 3. `services.py` — the use case, transactional and race-safe

```python
from django.core.exceptions import ValidationError
from django.db import transaction

from . import selectors
from .models import Batch, OrderLine


class OutOfStock(ValidationError):
    """Domain exception when there is not enough inventory."""
    pass


@transaction.atomic
def batch_allocate_line(*, orderid: str, sku: str, qty: int) -> str:
    """
    Allocate an order line to the highest-priority available batch.
    Transactional consistency + row locking against concurrent requests.
    """
    # 1. Create or fetch the line inside the transaction
    line, _ = OrderLine.objects.get_or_create(
        orderid=orderid,
        sku=sku,
        defaults={"qty": qty},
    )

    # 2. Candidates via the selector, rows locked against races
    candidate_batches = (
        selectors.batch_list_available_for_allocation(sku=sku)
        .select_for_update()
        .prefetch_related("allocations")
    )

    # 3. Business rule: first batch that can take the line
    selected_batch = next(
        (batch for batch in candidate_batches if batch.can_allocate(line)),
        None,
    )
    if not selected_batch:
        raise OutOfStock(f"No hay stock suficiente para el SKU {sku}")

    # 4. Mutate + persist
    line.batch = selected_batch
    line.qty = qty
    line.save(update_fields=["batch", "qty"])

    return selected_batch.reference
```

## 4. `api.py` — thin endpoint (django-ninja)

```python
from ninja import Router
from . import services

router = Router()


class OrderLineSchema(Schema):
    orderid: str
    sku: str
    qty: int


@router.post("/allocate")
def allocate_endpoint(request, payload: OrderLineSchema):
    try:
        batch_ref = services.batch_allocate_line(
            orderid=payload.orderid,
            sku=payload.sku,
            qty=payload.qty,
        )
    except services.OutOfStock as e:
        return 400, {"message": str(e)}
    return {"batch_reference": batch_ref}
```

The same service is callable from a classic Django view, an admin action,
or a management command with zero changes — that is the point of the
core/interface split.

## Why this beats a strict Repository layer in Django

1. **No double object layer** — model instances everywhere; no
   `BatchModel` ↔ `Batch` dataclass mapping to maintain.
2. **Aggregation in the engine** — `annotate`/`Sum`/`F` keep sums in SQL
   instead of loading thousands of rows into Python.
3. **Framework-native** — Django admin, signals, serializers and standard
   `TestCase`/pytest-django work without adapters.
