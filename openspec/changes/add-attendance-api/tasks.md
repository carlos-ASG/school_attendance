# Tasks: add-attendance-api

## 1. API app scaffold

- [x] 1.1 `uv add django-ninja`; create `src/api/` app package (`apps.py`, `__init__.py`) and append `api` to `module-name` in `pyproject.toml`; run `uv run manage.py check`
- [x] 1.2 Create `src/api/api.py` with `NinjaAPI(csrf=True, auth=<teacher auth callable>)` and mount it at `path("api/", api.urls)` in `src/config/urls.py`; add `ninja` to `INSTALLED_APPS` (bundled Swagger assets); confirm `/api/docs` serves
- [x] 1.3 Implement the teacher auth callable (unauthenticated → 401, no linked Teacher → 403, returns Teacher) reusing `get_teacher` from `teachers/views/mixins.py`

## 2. Bulk update endpoint

- [x] 2.1 Create `src/api/schemas.py`: `AttendanceRecordIn` (`id: int`, `status: AttendanceRecord.Status`, `notes: str`) and `AttendanceRecordBulkIn` (`records: list[...]`), plus the out-schema with `updated_at` for the response
- [x] 2.2 Implement `PATCH /api/sessions/{session_id}/records`: ownership-scoped session lookup (404), records fetched filtered to the session (unknown/foreign ids → 422 naming the offending entries), last-wins dedupe by id, `transaction.atomic()` with explicit `updated_at` + `bulk_update(['status', 'notes', 'updated_at'])`, 200 with saved records (Given/When/Then: valid batch saves all; invalid status → 422 nothing saved; foreign record → 422 nothing saved; other teacher's session → 404; duplicate id → last entry applied)
- [x] 2.3 Exercise the endpoint with a scripted Django test-client request (JSON payload, CSRF-exempt client or token header) asserting DB state and response codes; run `uv run manage.py check`

## 3. Toast component

- [x] 3.1 `uvx shadcn_django@latest add toast`; move generated files from project-root `templates/cotton/` into `src/core_ui/templates/cotton/`, translate user-visible copy to Spanish; rebuild Tailwind (`uv run manage.py tailwind build`) and mount the toast container in the today page template (content-specific Spanish titles → page-level, not base.html); added missing `[x-cloak]` rule to input.css

## 4. Today page rework (Alpine + endpoint)

- [x] 4.1 Make `TodaySessionDetailView` GET-only: drop `post()`/`_render_panel`, serialize the session's records (`id`, student display name, `status`, `notes`) into the template via `json_script`; delete `AttendanceFormSet` from `forms.py`
- [x] 4.2 Rewrite `today_session_detail.html`: rows rendered by `<template x-for>` from the hydrated records; status button uses `:class` with the existing `.status-*` classes and a JS label map; notes bound with `x-model` + change handler; collapse the `#attendance_panel` partialdef to plain markup and delete the `record_status_button` partialdef; remove the panel's messages `<ul>`
- [x] 4.3 Register the inline `attendancePanel` Alpine component (`alpine:init` hook in an inline `<script>`): `records` + `pending` (object keyed by id, starts empty), `cycle()` with the JS `STATUS_CYCLE` map, `markPending()`, `save()` → `fetch` PATCH with `X-CSRFToken` header, clear `pending` on 200 / preserve on failure
- [x] 4.4 Implement the unsaved-changes guard: save button disabled while `pending` is empty, pending-count badge, `beforeunload` handler setting both `preventDefault()` and `returnValue`, cleared after successful save
- [x] 4.5 Wire save feedback through the toast component (success and error toasts, Spanish copy); delete the dead HTMX paths: `RecordToggleStatusView`, `record_toggle_status` URL, its `views/__init__.py` re-export, and `STATUS_CYCLE`

## 5. Verification

- [x] 5.1 `uv run manage.py check`; manual pass on the today page: cycle statuses (no network requests in devtools), edit notes, verify badge count, save → toast + cleared badge, reload shows persisted values; failed-save path (e.g. stop server) preserves pending state
- [x] 5.2 Manual pass over unaffected flows: history page create/delete HTMX fragments, previous-session page batch edit, today-session delete dialog, `/api/docs` renders; `beforeunload` warning appears only with pending changes
