# Design: add-attendance-api

## Context

The today session page (`src/teachers/views/today_session.py`, `templates/teachers/today_session_detail.html`) currently persists attendance through two HTMX paths: `RecordToggleStatusView` saves a status to the DB on every button click and swaps the button fragment; a notes-only formset (`AttendanceFormSet`, `fields=('notes',)`) POSTs to `TodaySessionDetailView.post`, which re-renders the `#attendance_panel` fragment. Django-ninja is not installed; there is no JSON API layer. Auth is django-allauth session auth with a `Teacher` profile linked via `Teacher.user` (`get_teacher()` in `teachers/views/mixins.py`). Alpine.js is vendored and deferred-loaded in `base.html`; there is no custom JS anywhere yet (all Alpine usage is inline `x-data` in cotton components). CSRF token is already exposed to HTMX via `hx-headers` on `<body>` — that does not cover plain `fetch()`.

This change reverses the "saved per-action" decision from `split-session-detail-pages` (D5) for the today page only: statuses and notes now stage client-side and persist in one explicit batch save. These deltas are written against the post-split spec state (that change is code-complete; it should be archived before this one).

## Goals / Non-Goals

**Goals:**
- One batch-save path for today-page attendance: Alpine stages changes locally, one `fetch` saves them via a django-ninja endpoint.
- Status clicks with zero network round-trips.
- First API app (`src/api/`) as the home for future programmatic endpoints.
- Unsaved-changes safety: unload warning, pending-count badge, disabled save button.
- Toast feedback for save success/error.

**Non-Goals:**
- Migrating the previous-session page's batch edit form onto the API (later change; endpoint deliberately supports it).
- GET/read endpoints, API versioning, token or third-party auth.
- Model, migration, or `attendance-tracking` rule changes.
- Touching history-page or delete-session HTMX flows.

## Decisions

### D1: New `api` app hosts a `NinjaAPI(csrf=True)` mounted at `/api/`
Plain app package `src/api/` with `api.py` + `schemas.py` (no models/templates → `INSTALLED_APPS` registration optional; we add `ninja` there anyway to bundle Swagger assets instead of loading them from a CDN). `NinjaAPI(csrf=True)` is mandatory because auth is session-cookie based — ninja's CSRF protection is otherwise off by default. Mounted via `path("api/", api.urls)` in `config/urls.py`. The app must be appended to `module-name` in `pyproject.toml` for the `uv_build` packaging (same mechanism as `teachers`).
*Alternative considered*: endpoints inside `teachers/` — rejected: the API is not teacher-panel-specific (any teacher-owned session), and a clean app boundary keeps future non-panel endpoints out of the panel app.

### D2: Teacher auth as a ninja auth callable reusing `get_teacher()`
A small auth function (in `src/api/`, importing `get_teacher` from `teachers.views.mixins`): unauthenticated → 401; authenticated without linked `Teacher` → 403; otherwise returns the `Teacher` (lands in `request.auth`). Mirrors `TeacherRequiredMixin` semantics; no `PermissionDenied` exception flow needed.
*Alternative considered*: django-ninja's `django_auth` — rejected: it authenticates but has no Teacher-profile check; we'd still need a custom layer, so one callable does both.

### D3: `PATCH /api/sessions/{session_id}/records` with path param, full-record payload
Session id is a **path** parameter (RESTful; supersedes the original query-param sketch). Body schema:

- `AttendanceRecordIn`: `id: int`, `status: AttendanceRecord.Status` (Django TextChoices validate directly as a pydantic enum), `notes: str` — **always sent in full** (no patch semantics); Alpine holds the complete record state, so full payloads keep the contract simple and the server response authoritative.
- `AttendanceRecordBulkIn`: `records: list[AttendanceRecordIn]` (the "list schema").

Handler flow: get session scoped by ownership (`AttendanceSession.objects.select_related('course').get(pk=..., course__teacher=teacher)`, missing → 404); fetch payload records filtered to the session; unknown/foreign record ids → 422 identifying the offending entries; dedupe by id with **last-wins** (client already dedupes via the `pending` map — this is server-side belt-and-suspenders); `transaction.atomic()` + `bulk_update(records, ['status', 'notes', 'updated_at'])`; respond 200 with the saved records (serialized through an out-schema including `updated_at`) so the client can reconcile.
*Alternatives considered*: query param for session id (original sketch — works, but path param reads better and costs nothing); patch semantics with optional `notes` (only pays off if payloads could be partial — they can't, per D3's full-record rule); per-record best-effort save (rejected: partial saves would desync the client's `pending` state).

### D4: Skip `full_clean()` in the endpoint
`AttendanceRecord.full_clean()` runs a group-membership query per record (N+1) and validates nothing that a status/notes update can violate: the status enum is enforced by the schema, notes is an unconstrained text field, and the student-in-group rule is untouched by this update path (records already belong to the session).
*Alternative considered*: calling `full_clean()` for defense-in-depth — rejected: silent N+1 per save for zero additional validation on the mutable fields.

### D5: Alpine owns the rows (`x-for` over hydrated JSON); formset machinery dies
The GET view serializes the session's records (`id`, student display name, `status`, `notes`) into the template via Django's built-in `json_script` filter; an `Alpine.data('attendancePanel', ...)` component (registered from an **inline `<script>` in the page template** on `alpine:init`, since `alpine.min.js` is deferred and there is no custom JS file yet) reads it in `init()`. State: `records` (authoritative list) + `pending` (**object keyed by record id** — the "void list" that starts empty; keyed so repeated clicks on one student collapse to one entry). `cycle(record)` advances status via a JS `STATUS_CYCLE` map, `markPending(record)` stages note edits; `save()` POSTs `Object.values(pending)` with `fetch` (`X-CSRFToken` header seeded from `{{ csrf_token }}`), clears `pending` on 200, keeps it on failure. Rows render in `<template x-for>` with one root element — cotton tags render server-side and compose fine inside the loop body. Status styling reuses the existing `.status-btn .status-<lower>` classes from `teachers/css/panel.css` via `:class`; a small JS label map replaces `get_status_display`.
*Alternatives considered*: keep server-rendered formset rows with an Alpine overlay — rejected: the formset becomes vestigial and two sources of truth persist; external static JS file — rejected for now (LoB; extract later if the component grows).
*Note*: the page is already JS-dependent (HTMX), so there is no no-JS regression; expect a brief empty-table flash before Alpine boots (acceptable; mitigate with `x-cloak` if it is noticeable).

### D6: Today-page view becomes GET-only; the removed pieces stay removed
`TodaySessionDetailView` loses `post()`/`_render_panel` (GET-only DetailView that also supplies the serialized records). Deleted: `RecordToggleStatusView` + `record_toggle_status` URL + `views/__init__.py` re-export, `STATUS_CYCLE` (→ JS), `AttendanceFormSet` in `forms.py` (`AttendanceEditFormSet` for the previous page survives), `record_status_button` partialdef, and the panel's messages `<ul>` (base.html already renders messages; the copy only existed for HTMX panel swaps). With both save paths gone, `#attendance_panel` is never rendered in isolation — its partialdef collapses to plain inline markup; `session_header` stays as-is.

### D7: Unsaved-changes guard is client-side scope, required not polish
Disabled save button when `pending` is empty; badge with pending count; `beforeunload` handler registered when `pending` is non-empty — must set **both** `event.preventDefault()` and `event.returnValue` to warn reliably across browsers. Cleared after a successful save. Failure path preserves `pending` so a retry re-sends the same data.

### D8: shadcn toast for save feedback
`uvx shadcn_django@latest add toast`, sources moved into `src/core_ui/templates/cotton/` per repo convention (CLI writes to project-root `templates/cotton/`), copy translated to Spanish. The toast is Alpine-store based; `attendancePanel.save()` pushes success/error events into it. Server-side django `messages` are no longer used on this page's save path.

## Risks / Trade-offs

- [Data loss on abandon: changes are no longer persisted per click] → required guard (D7): unload warning + visible pending badge; save-on-failure keeps `pending` intact for retry.
- [Two-tab edits on the same session: last save wins per record, silently] → pre-existing risk (formset had the same semantics), unchanged; accepted for a single-teacher-per-course domain.
- [Client holds optimistic state the DB may not reflect between toggle and save] → `pending` carries the same values; a failed save keeps it staged; response records reconcile state on success.
- [Empty-table flash before Alpine boots] → acceptable on an already JS-dependent page; `x-cloak` fallback if visible in practice.
- [JS/Python status-label duplication (Spanish labels + cycle map in JS)] → small, stable constant; drift would be caught immediately by visible wrong labels in manual verification.
- [bulk_update bypasses auto_now] → handler sets `updated_at` explicitly before `bulk_update` (D3); verified by the response's authoritative `updated_at`.

## Migration Plan

1. Add dependency + `api` app skeleton, mount at `/api/` (additive; existing behavior untouched).
2. Add endpoint + toast component (additive).
3. Rework the today page onto Alpine + endpoint; delete the toggle view/URL and formset path (the only behavior-breaking step — no-deploy rollback is `git revert` of this commit range; there are no migrations or data changes to unwind).
4. Verify: `uv run manage.py check`, manual pass over the today page (toggle → badge → save → toast; failed-save path; unload guard), plus a scripted JSON request against the endpoint (test client) asserting the DB state.

## Open Questions

None — all forks resolved during exploration (Forks 1–7: Alpine ownership = A, full payload, guard in scope, path param, any-date sessions, toast, `api` name + inline script).
