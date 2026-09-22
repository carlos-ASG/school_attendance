# Tasks: freeze-past-cycle-sessions

## 1. Shared freeze rule

- [x] 1.1 Given a session whose course's cycle contains today, When the shared predicate in `src/school/calendar.py` is consulted, Then it reports not frozen; and Given a session whose cycle ended, a cycle-less course, or today in a gap between cycles, Then it reports frozen (unit tests in `src/school/tests.py` with two-cycle fixtures via `make_cycle`)
- [x] 1.2 Define the shared Spanish error message next to the predicate so panel and API surfaces use one string

## 2. Teacher panel views

- [x] 2.1 Given `PreviousSessionDetailView`, When loading a session, Then `get_queryset` selects `course__school_cycle` and the view computes one `session_is_editable` context flag
- [x] 2.2 Given a frozen session, When the page is opened with `?edit=1`, Then the read-only partial renders (edit mode suppressed)
- [x] 2.3 Given a frozen session, When the edit formset is POSTed (HTMX and non-HTMX), Then nothing is saved, an error message is set, and the read-only partial re-renders into `#attendance-panel` / a redirect to the session detail URL
- [x] 2.4 Given `SessionDeleteView`, When deleting a frozen session (HTMX and non-HTMX), Then the session is not removed, an error message is set, and the session list re-renders / a redirect to the history page; add `course__school_cycle` to its lookup
- [x] 2.5 Panel tests in `src/teacher_panel/tests.py`: frozen GET stays read-only, frozen POST rejected, frozen delete rejected, active-cycle session still editable and deletable (two-cycle fixture)

## 3. Session page header UI

- [x] 3.1 Given a frozen session, When the header renders, Then the pencil button becomes a `c-alert-dialog` trigger opening a "Sesión de solo lectura" dialog that names the cycle and its date range with a single "Entendido" action
- [x] 3.2 Given a frozen session, When the header renders, Then the trash button is not rendered; Given an editable session, Then both buttons behave exactly as before
- [x] 3.3 Run `uv run manage.py tailwind build` (alert-dialog classes are already in the prebuilt CSS; verify no new utility classes are required, rebuild if any were added)

## 4. Bulk-update API

- [x] 4.1 Given a frozen session owned by the requesting teacher, When `PATCH /sessions/{id}/records` is sent, Then the endpoint responds 422 with the shared read-only message and no records change (add `course__school_cycle` to the session lookup)
- [x] 4.2 API tests in `src/api/tests.py`: replace/augment `test_past_session_update_allowed` with a past-in-active-cycle session (200, still allowed) and a past-frozen-cycle session (422, unchanged records)

## 5. Verification

- [x] 5.1 Given all changes, When `uv run manage.py check` runs, Then it passes with no issues
- [x] 5.2 Given the full test suite, When `uv run manage.py test` runs (school, teacher_panel, api), Then every test passes including the pre-existing `test_existing_session_survives_later_calendar_change`
