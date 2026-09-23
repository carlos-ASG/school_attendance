# Selectors: reads, aggregation, N+1 avoidance

Selectors are the single place that decides *how* data is fetched and
optimized. The rest of the app never builds domain queries inline.

## Rules

- Functions named `<entity>_<action>`: `batch_get_by_reference`,
  `batch_list_available_for_allocation`, `user_list`.
- Keyword-only args (`def f(*, ...)`), type-annotated, return
  `QuerySet[Model]` / `Optional[Model]` / whatever the caller needs.
- **Never mutate.** No `save()`, no `update()`, no `delete()`, no
  `select_for_update()` — that's the service's job (a service may append
  `.select_for_update()` to the selector's queryset).
- A selector may call other selectors. It never calls a service.
- Accept a `filters` dict for list endpoints; apply conditionally:

```python
def user_list(*, filters: dict | None = None) -> QuerySet[BaseUser]:
    filters = filters or {}
    qs = BaseUser.objects.all()

    if (email := filters.get("email")) is not None:
        qs = qs.filter(email__icontains=email)
    if (is_admin := filters.get("is_admin")) is not None:
        qs = qs.filter(is_admin=is_admin)

    return qs
```

## Single-object fetch with prefetch

```python
from typing import Optional


def batch_get_by_reference(*, reference: str) -> Optional[Batch]:
    """Fetch a Batch by reference, allocations prefetched."""
    return (
        Batch.objects.filter(reference=reference)
        .prefetch_related("allocations")
        .first()
    )
```

- Return `None` (`.first()`) or raise `DoesNotExist` in dedicated
  `_get_*` selectors when the caller treats absence as an error.

## Aggregate in SQL, not Python

Push sums/counts to the database with `annotate` + `F` + `Coalesce`:

```python
from django.db.models import QuerySet, F, Sum
from django.db.models.functions import Coalesce


def batch_list_available_for_allocation(*, sku: str) -> QuerySet[Batch]:
    """
    Batches with stock left for a SKU, ordered by business priority:
    1. In-stock batches first (eta is None).
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

Why: `sum(line.qty for line in batch.allocations.all())` per instance is
fine once, but in a list of 100 batches it is 100 extra queries plus
Python-side summation. The annotated queryset is one query, filterable and
sortable on the computed value.

## N+1 avoidance checklist

- To-many relations read together: `prefetch_related`
- FK/one-to-one read together: `select_related`
- `only()` / `defer()` only when profiling justifies it (they add
  deferred-load traps).
- Serializing a computed value across a relation → make it an
  `annotate(...)`, not a model property that hits the DB per row.
- `Meta.ordering` can silently add `ORDER BY` (and cost) to every query —
  prefer explicit `.order_by(...)` in the selector when the order is a
  business rule.

## Testing selectors

Test against the database (unlike `clean()` tests): create state with
services/factories, assert on membership, ordering, and the annotated
values. Check query counts (`assertNumQueries`) when the point of the
selector is optimization.
