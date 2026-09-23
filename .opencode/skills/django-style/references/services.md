# Services: atomicity, row locking, domain exceptions

Services are where use cases live: writes, cross-model orchestration, calls
to external systems. Everything else (views, APIs, admin, management
commands) delegates to them.

## Rules

- Functions named `<entity>_<action>`: `batch_allocate_line`,
  `user_create`. Keyword-only args (`def f(*, ...)`), type-annotated.
- `@transaction.atomic` around anything that writes more than trivially —
  and around anything that needs `select_for_update`.
- `obj.full_clean()` immediately before `obj.save()` — constraints and
  `clean()` then raise `ValidationError` instead of `IntegrityError`.
- Compose: a service calls selectors and other services.
- Class-based services when you need a namespace or a multi-step flow
  (create/update, start/finish).

## Canonical create service

```python
@transaction.atomic
def course_create(*, name: str, start_date: date, end_date: date) -> Course:
    obj = Course(name=name, start_date=start_date, end_date=end_date)

    obj.full_clean()
    obj.save()

    return obj
```

Note: construct → `full_clean()` → `save()`, not `Model.objects.create(...)`
(which skips validation).

## Domain exceptions

Business failures are exception subclasses the caller can catch and
translate (HTTP 400, admin error message, CLI exit code):

```python
from django.core.exceptions import ValidationError


class OutOfStock(ValidationError):
    """Domain exception: not enough inventory."""
```

Catch them in the API/view — never let them leak as 500s, and never catch
them inside the service to return booleans; exceptions keep the happy path
readable and composable.

## Concurrency: `select_for_update` + `atomic`

Two requests allocating the same stock must serialize. Lock the rows you
are about to decide on, inside the transaction:

```python
@transaction.atomic
def batch_allocate_line(*, orderid: str, sku: str, qty: int) -> str:
    line, _ = OrderLine.objects.get_or_create(
        orderid=orderid,
        sku=sku,
        defaults={"qty": qty},
    )

    candidate_batches = (
        selectors.batch_list_available_for_allocation(sku=sku)
        .select_for_update()                    # lock candidate rows
        .prefetch_related("allocations")
    )

    selected_batch = next(
        (batch for batch in candidate_batches if batch.can_allocate(line)),
        None,
    )
    if not selected_batch:
        raise OutOfStock(f"No hay stock suficiente para el SKU {sku}")

    line.batch = selected_batch
    line.qty = qty
    line.save(update_fields=["batch", "qty"])

    return selected_batch.reference
```

Key points:

- The lock applies to the **selector's queryset** — one reason selectors
  must return `QuerySet` (still lazy/composable), not materialized lists.
- `select_for_update()` **must** run inside `transaction.atomic`; outside
  it, Django raises `TransactionManagementError`.
- Only the main query's rows are locked — `prefetch_related` rows are NOT
  locked.
- Lock ordering: when a use case locks multiple row sets, order them
  consistently (e.g. by pk) to avoid deadlocks.

## Updates

Fetch → mutate → `full_clean()` → `save(update_fields=[...])`. A dedicated
`<entity>_update` service beats a generic one; it documents exactly which
fields the use case owns:

```python
@transaction.atomic
def token_rotate(*, token: Token) -> Token:
    token.set_new_secret()
    token.full_clean()
    token.save(update_fields=["secret", "expiry", "updated_at"])
    return token
```

## Async side effects

Schedule tasks/emails only after a successful commit:

```python
transaction.on_commit(lambda: payment_charge.delay(payment_id=payment.id))
```

Otherwise the worker may race the transaction and not see the row.

## Class-based services

Use for namespaces (create + update sharing private helpers) or flows
(start → upload → finish):

```python
class FileStandardUploadService:
    def __init__(self, user: BaseUser, file_obj):
        self.user = user
        self.file_obj = file_obj

    @transaction.atomic
    def create(self, *, file_name: str = "") -> File:
        _validate_file_size(self.file_obj)
        obj = File(...)
        obj.full_clean()
        obj.save()
        return obj
```

The API constructs it with `request.user` / `request.FILES[...]` and calls
`create()`. The Django admin can reuse the same class in `save_model`.

## Testing services

- Cover business logic exhaustively; hit the real database.
- Mock what leaves the project: Celery tasks (`@patch('...tasks.x.delay')`),
  emails, HTTP.
- Mock selectors only when they already have their own tests and the
  service test needs a specific return value.
- Build state with services, factories (`factory_boy`), or plain
  `Model.objects.create()` — whatever is already in the repo.
- Assert domain exceptions with `assertRaises` and verify state changes
  (row counts, field values).
