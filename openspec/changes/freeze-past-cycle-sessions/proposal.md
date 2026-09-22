# Proposal: freeze-past-cycle-sessions

## Why

Teachers can still edit (and delete) attendance sessions that belong to a school cycle
that is no longer active. Once a cycle ends, its attendance records are historical and
must stay immutable; today the panel edit form, the panel delete action, and the
bulk-update API all accept past-cycle sessions without any cycle check.

## What Changes

- Define a single freeze rule: a session is editable/deletable only when the session's
  course's cycle contains today's date (`session.course.school_cycle.contains_date(today)`).
  Sessions whose cycle has ended (or when today falls in a gap between cycles) become
  read-only.
- `PreviousSessionDetailView`: `?edit=1` no longer enables edit mode for frozen sessions
  (renders read-only instead); POSTing the edit formset is rejected with an error
  message and the read-only panel re-rendered (HTMX retarget, same shape as the
  invalid-formset path).
- `SessionDeleteView`: deleting a frozen session is rejected with an error message;
  list re-rendered/redirect as today.
- Bulk-update API (`api:update_session_records`): frozen sessions are rejected (422)
  instead of the current "any owned session regardless of date" behavior.
- `previous_session_detail.html` header: for frozen sessions the pencil button opens a
  `c-alert-dialog` explaining the session is read-only (belongs to a past cycle); the
  trash button is simply hidden.
- Model `clean()` is untouched: cycle-freshness is view/API policy, not data validity
  (existing sessions must survive later calendar changes).

## Capabilities

### New Capabilities

(none — the freeze rule is added as a new requirement inside `attendance-tracking`)

### Modified Capabilities

- `attendance-tracking`: new requirement "Attendance editing restricted to the active
  cycle" (the domain-level freeze rule); the existing "Attendance editing" requirement
  gains the cycle-freshness condition.
- `teacher-panel`: "Past session review and correction" gains frozen-session scenarios
  (read-only despite `?edit=1`, POST rejected, notice dialog on the pencil button);
  "Session deletion from the panel" gains the frozen-delete-rejected scenario and the
  hidden trash button.
- `attendance-api`: "Any owned session is editable regardless of date" is replaced —
  frozen sessions are rejected with 422; past sessions inside the active cycle remain
  editable.

## Impact

- Views: `src/teacher_panel/views/session_detail.py`, `src/teacher_panel/views/course_session_history.py`
  (add `course__school_cycle` to `select_related`).
- API: `src/api/endpoints/attendance.py`.
- Template: `src/teacher_panel/templates/teacher_panel/previous_session_detail.html`
  (session header partial only).
- Tests: `src/teacher_panel/tests.py`, `src/api/tests.py`, `src/school/tests.py`
  (two-cycle fixtures via existing `make_cycle`).
- No model/migration changes; no new cotton components; admin remains unrestricted.

## Non-goals

- Restricting the Django admin (admins keep full edit/delete power).
- Freezing today-session editing (always inside the active cycle by construction).
- Adding a `frozen` boolean column or touching `AttendanceSession.clean()`.
- New modal components — reuses the existing `c-alert-dialog`.
