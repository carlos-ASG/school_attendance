# Proposal: add-attendance-api

## Why

Today's session page persists every status click immediately over HTMX (one DB write per click, one fragment re-render) while notes take a separate formset path. The Teacher cannot rehearse a full attendance pass and save once — and the interaction pays a network round-trip on every tap. We want client-side staging (Alpine) with one explicit batch save through a JSON API, which also gives the project its first django-ninja endpoint layer for future programmatic access.

## What Changes

- **New `api` Django app** hosting django-ninja endpoints (`NinjaAPI(csrf=True)` mounted at `/api/`), session-cookie auth restricted to users linked to a Teacher.
- **New bulk update endpoint**: `PATCH /api/sessions/{session_id}/records` — accepts `{ records: [{id, status, notes}, ...] }`, validates ownership and that every record belongs to the session, saves atomically, returns the saved records. Works for any session owned by the teacher (today or past).
- **Today session page refactored to Alpine-owned UI**: the view serializes records to JSON (`json_script`); Alpine renders the rows (`x-for`), cycles statuses purely client-side, and buffers changes in a `pending` map — status clicks make NO network request. The save button POSTs the pending records to the new endpoint via `fetch`.
- **Unsaved-changes guard**: `beforeunload` warning while pending changes exist, an "N sin guardar" badge, and a disabled save button when nothing is pending.
- **Feedback via toast**: adds the shadcn toast component for save success/error messages (replaces server-rendered messages on this page).
- **BREAKING** (panel-internal): status clicks no longer persist immediately; persistence now happens only on explicit save.
- **Removed**: `RecordToggleStatusView` + `record_toggle_status` URL, `STATUS_CYCLE` (moves to JS), `AttendanceFormSet` (notes-only formset), `TodaySessionDetailView.post`/`_render_panel` (view becomes GET-only), `record_status_button` partialdef, attendance-panel HTMX swap.

## Capabilities

### New Capabilities

- `attendance-api`: JSON API for attendance record updates — teacher session-cookie auth with CSRF, session-scoped bulk record updates with ownership and membership validation, atomic saves.

### Modified Capabilities

- `teacher-panel`: today session page re-records interaction requirements — client-side status cycling with pending-changes buffer, single explicit batch save through the JSON API, unsaved-changes guard, toast feedback; per-action HTMX persistence requirement and its fragments are removed.

## Impact

- `src/api/` (new app): `api.py`, `schemas.py`; mounted in `src/config/urls.py`; added to `module-name` in `pyproject.toml` (+ optional `INSTALLED_APPS` entry for bundled Swagger assets).
- `src/teachers/`: `views/today_session.py` (GET-only view, toggle view deleted), `views/__init__.py`, `forms.py` (AttendanceFormSet removed), `urls.py`, `templates/teachers/today_session_detail.html` (Alpine rows, inline `<script>` with `alpine:init` component registration).
- `src/core_ui/`: toast component added via `uvx shadcn_django@latest add toast`.
- Dependencies: `uv add django-ninja` (not currently installed). No model, migration, or admin changes.

## Non-goals

- No migration of the previous-session page's batch edit form onto the API (door left open; separate change).
- No GET/read endpoints, no API versioning, no token/third-party auth — session cookie + CSRF only.
- No model changes, migrations, or `attendance-tracking` rule changes (records remain editable, statuses unchanged).
- No changes to history-page or delete-session HTMX flows.
