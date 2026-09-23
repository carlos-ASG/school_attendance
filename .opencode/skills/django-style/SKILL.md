---
name: django-style
description: Use when writing or reviewing Django business logic layering — services.py (writes, transaction.atomic, select_for_update), selectors.py (reads, querysets, annotate/F), model properties vs selectors, thin views/APIs, domain exceptions — or when the user mentions services, selectors, or the HackSoft Django-Styleguide.
license: MIT
---

# Django Style: Services & Selectors

Structure Django business logic after the HackSoft Django-Styleguide
(https://github.com/HackSoftware/Django-Styleguide): embrace Django's Active
Record nature instead of fighting it with a Repository/dataclass layer.

Run everything via `uv run manage.py <cmd>`. Apps live under `src/<app>/`.

## The core rule

Business logic lives in **services** (writes), **selectors** (reads), simple
**model properties/methods**, and model `clean()`/constraints. It does NOT
live in views, API handlers, serializers, forms, model `save()` overrides,
custom managers, or signals. Views and serializers are *interfaces*; services
and selectors are the *core*. Changing the interface (ninja API → management
command → admin action) must never require rewriting the logic.

| Layer          | Contains                                                        | Never contains                    |
| -------------- | --------------------------------------------------------------- | --------------------------------- |
| `models.py`    | Fields, `Meta.constraints`, simple properties/methods, `clean`  | Cross-model orchestration         |
| `selectors.py` | Read-only queries; returns `QuerySet` / model instances         | Mutations, `save()`, writes       |
| `services.py`  | Writes & use-case orchestration, `@transaction.atomic`          | — (this IS the domain layer)      |
| views / `api.py` | Deserialize input, call selector/service, catch exceptions    | Business rules, queries of record |

## Services (`services.py`)

- Plain functions named `<entity>_<action>`: `batch_allocate_line`,
  `user_create`. Greppable and self-namespacing.
- Keyword-only arguments (`def f(*, ...)`), type-annotated.
- Wrap use cases in `@transaction.atomic`; combine with
  `select_for_update()` on the rows being mutated to prevent race
  conditions (see `references/services.md`).
- Validate with `obj.full_clean()` right before `save()` — Django >= 4.1
  then also checks `Meta.constraints`.
- Raise domain exceptions (subclasses of `ValidationError`) for business
  failures; callers translate them to HTTP 400 etc.
- A service may call selectors and other services. A selector never calls
  a service.
- Class-based services are fine for namespaces/flows (create+update,
  start+finish).

## Selectors (`selectors.py`)

- Read-only functions, same naming/annotation rules as services.
- Return `QuerySet` (composable, lazy) or a model instance / `Optional[Model]`.
- Centralize filters and optimizations here: `select_related`,
  `prefetch_related`, `annotate` + `F` + `Coalesce(Sum(...))` so aggregates
  run in SQL, not Python (see `references/selectors.md`).
- Services may append `.select_for_update()` to a selector's queryset to
  lock rows inside a transaction.
- Filtering for list APIs: selector takes `filters: dict` and applies them
  (django-filter's `FilterSet` if it grows).

## Model properties vs selectors vs services

- Simple derived value from **non-relational** fields, cheap calculation →
  model `@property` (serializes easily, template-friendly).
- Needs an argument, still simple → model **method**.
- Spans multiple relations, needs fetching, or can cause N+1 when
  serialized → **selector** (annotate in SQL).
- Writes anything or orchestrates across models → **service**.
- Simple multi-field validation → model `clean()`; complex or
  relation-spanning validation → service. Prefer `Meta.constraints`
  (`CheckConstraint`, `UniqueConstraint`) whenever expressible — the
  database enforces them no matter who writes.

## Thin consumption

```python
# api.py (django-ninja) — deserialize, delegate, translate errors
from ninja import Router
from . import services

router = Router()

@router.post("/allocate")
def allocate_endpoint(request, payload: OrderLineSchema):
    try:
        batch_ref = services.batch_allocate_line(
            orderid=payload.orderid, sku=payload.sku, qty=payload.qty,
        )
    except services.OutOfStock as e:
        return 400, {"message": str(e)}
    return {"batch_reference": batch_ref}
```

Same shape for views, admin actions, and management commands. Co-load the
`django-ninja` skill when the consumer is a ninja API.

## Why not a strict Repository layer in Django

1. No double layer of objects — work with model instances directly; no
   `BatchModel` → dataclass `Batch` mapping and back.
2. Aggregations (`annotate`, `Sum`, `F()`) resolve in the database engine
   instead of pulling thousands of rows into Python.
3. Zero friction with the Django admin, signals, serializers, and standard
   `TestCase` / pytest-django testing.

## Detailed references

| Topic                                                       | File                        |
| ----------------------------------------------------------- | --------------------------- |
| Models: constraints, `clean`/`full_clean`, properties/methods | `references/models.md`     |
| Selectors: aggregation, ordering, N+1 avoidance              | `references/selectors.md`  |
| Services: atomicity, row locking, domain exceptions          | `references/services.md`   |

## Examples

| Example                                        | File                            |
| ---------------------------------------------- | ------------------------------- |
| Full allocation flow (models → selector → service → API) | `examples/allocation-flow.md` |

## Gotchas

- **Never mutate in a selector** — it breaks the read/write split that makes
  the layer auditable.
- **`select_for_update()` only works inside a transaction**; outside
  `atomic` it raises or silently no-ops (backend-dependent).
- Locking a queryset with `prefetch_related` does NOT lock the prefetched
  rows — only the main query's rows are locked.
- `Model.objects.create(...)` skips `full_clean` → `constraints` failures
  surface as `IntegrityError`, not `ValidationError`. Validate first.
- Services with async side effects (Celery, emails): schedule via
  `transaction.on_commit(...)` so tasks only fire after a successful commit.
- Don't logic in signals — reserve them for decoupled notification/cache
  invalidation.
