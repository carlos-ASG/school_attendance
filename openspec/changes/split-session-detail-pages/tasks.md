# Tasks: split-session-detail-pages

## 1. Forms

- [x] 1.1 Given `SessionForm`, when a date >= today is submitted, then validation rejects it (future: existing message; today: message directing to the "Sesión de hoy" card); drop the `exclude_pk` parameter (update flow removed)
- [x] 1.2 Given `AttendanceRecord`, when the previous-page edit form is rendered, then a new `AttendanceEditFormSet` (modelformset, fields `status` + `notes`, status widget = select/combobox with the four statuses) is available alongside the unchanged notes-only `AttendanceFormSet`

## 2. Status selector component

- [x] 2.1 Given the shadcn_django CLI, when adding the combobox (or select) component, then source lands in `src/core_ui/templates/cotton/` (moved from project-root `templates/cotton/`) and renders standalone
- [x] 2.2 Given the component inside a formset row, when the teacher picks a status, then a hidden input named `form-<i>-status` carries the value and submits with the form; if formset serialization fights the component, then fall back to a shadcn-styled native `<select>` (probe with a render/submit script before building the full template)

## 3. Views and URLs

- [x] 3.1 Given `urls.py`, when re-wiring, then `courses/<pk>/sessions/today/` (today_session_create, POST), `sessions/<pk>/today/` (today_session_detail) exist, `session_edit` is removed, and `session_detail`/`session_delete`/`record_toggle_status` remain
- [x] 3.2 Given `views/today_session.py` (new module), when a teacher POSTs the get-or-create endpoint, then today's session is created (with records) or reused and the teacher is redirected to `sessions/<pk>/today/` (move the logic out of `CourseDetailView._create_today_session`)
- [x] 3.3 Given `views/today_session.py`, when the today session page is opened for a session not dated today, then it redirects to `sessions/<pk>/`; when opened for today's session, then it renders always-editable and its POST saves the notes formset, re-rendering `today_session_detail.html#attendance_panel` (repo HTMX patterns)
- [x] 3.4 Given `views/session_detail.py` becomes the previous-page module, when the previous session page is opened for a session dated today, then it redirects to `sessions/<pk>/today/`; otherwise it renders read-only (`?edit=1` renders the batch edit form) and its POST saves `AttendanceEditFormSet` and renders `#attendance_readonly` (drop to read-only with confirmation)
- [x] 3.5 Given `RecordToggleStatusView` moves to `views/today_session.py`, when a record toggles, then it renders `today_session_detail.html#record_status_button` unconditionally (today page only)
- [x] 3.6 Given date editing is removed, when cleaning up, then `SessionUpdateView`, the `session_edit` URL, and any date-change helpers are deleted
- [x] 3.7 Given `SessionDeleteView` moves to `views/course_session_history.py`, when a past session is deleted via HTMX, then the response re-renders `course_session_history.html#session_list` with the fresh queryset; when a today session is deleted, then the response redirects to the course detail page; non-HTMX fallback stays a redirect to the history page
- [x] 3.8 Given `CourseSessionHistoryView`, when the create form POSTs, then its `post()` validates `SessionForm`, creates the session + records and redirects to the new session's page; HTMX errors re-render `#session_create_form` + `retarget`; the list queryset excludes sessions dated today
- [x] 3.9 Given `CourseDetailView`, when cleanup finishes, then `post()`, `dispatch()` form stashing and `_create_today_session()` are deleted (pure `DetailView`)
- [x] 3.10 Given `views/__init__.py`, when the modules are reorganized, then all view classes re-export cleanly and `uv run manage.py check` passes

## 4. Templates

- [x] 4.1 Given the split, when `today_session_detail.html` is created, then it hosts `#session_header` (back link to course detail), `#attendance_panel` (cyclic status buttons + notes formset + delete alert dialog redirecting to course detail on success) and `#record_status_button` — always editable, no date-change control
- [x] 4.2 Given the split, when `previous_session_detail.html` is created, then it hosts `#session_header` (back link to history + "Editar" control → `?edit=1`), `#attendance_readonly`, and `#attendance_edit_form` (batch form: student, status selector, notes, single submit) — no `session_form` fragment
- [x] 4.3 Given the old template, when the split is complete, then `session_detail.html` is deleted and no stale references remain (grep `session_detail.html#`, `session_edit`, `session_panel`, `session_form`)
- [x] 4.4 Given the history page, when restructured, then a top shadcn card hosts the "Crear sesión en otra fecha" form with a `#session_create_form` partialdef for HTMX error re-renders
- [x] 4.5 Given the history table, when restructured, then columns are Date (plain text) | Created | Acciones ([Ver] button → previous session page; [Eliminar] `c-alert-dialog` → `hx-post` delete targeting `#session-list`)
- [x] 4.6 Given the course detail page, when restructured, then the `session_panel` partialdef is removed and a "Sesión de hoy" compact card (POST to the get-or-create endpoint) plus the history link remain
- [x] 4.7 Given the dashboard, when restructured, then under each course card a `grid grid-cols-2` row renders the "Sesión de hoy" compact card (footer button POSTing to the get-or-create endpoint) and the "Historial de sesiones" card (link to history)

## 5. Verification

- [x] 5.1 Given the full change, when running `uv run manage.py check`, then it passes with no errors
- [x] 5.2 Given a test-client smoke script (copied dev DB, per the django6-htmx harness), when exercising every flow, then: dashboard card get-or-creates and redirects; URL guards redirect both ways; history create accepts past and rejects today/future/duplicate dates with in-place form errors; previous page opens read-only, `?edit=1` renders the batch form, submit saves all rows and drops to read-only; today page toggle returns only the button fragment; deleting a past session re-renders the list (incl. empty state); deleting a today session redirects to course detail; the history list never includes today's session
- [x] 5.3 Given the Spanish-copy rule, when reviewing all new/changed templates, then every user-visible string is in Spanish
