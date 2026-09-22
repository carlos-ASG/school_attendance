# Design: freeze-past-cycle-sessions

## Context

A session's cycle is never stored on the session — it is reached through
`session.course.school_cycle` (a `SchoolCycle` with `start_date`/`end_date` and
`contains_date()`, validated non-overlapping). Four write paths currently accept any
owned session with no cycle check:

1. `PreviousSessionDetailView.get_context_data` — `?edit=1` always enables edit mode
   (src/teacher_panel/views/session_detail.py:42).
2. `PreviousSessionDetailView.post` — saves the formset unconditionally (:60).
3. `SessionDeleteView.post` — deletes unconditionally
   (src/teacher_panel/views/course_session_history.py:81).
4. API `update_session_records` — bulk-updates records of any owned session
   (src/api/endpoints/attendance.py:25); its spec guarantees "any owned session
   regardless of date" and `test_past_session_update_allowed` (src/api/tests.py:197)
   pins that behavior.

Today-session editing (the same API endpoint) is safe by construction: today sessions
only exist after `validate_session_date` passed, so their course's cycle always
contains today.

`AttendanceSession.clean()` deliberately skips cycle validation on edits
(`if self._state.adding`, attendance_session.py:59) so existing sessions survive later
calendar changes — that behavior must stay.

## Goals / Non-Goals

**Goals:**

- One shared freeze rule applied at every teacher-facing write path (panel edit, panel
  delete, bulk-update API).
- Frozen sessions render read-only with a clear explanation (alert dialog on the
  pencil button; trash button hidden).
- Existing behavior preserved for sessions inside the active cycle.

**Non-Goals:**

- Restricting the Django admin.
- Model-level validation or schema changes.
- New cotton/modal components.

## Decisions

### D1 — Freeze rule: `session.course.school_cycle.contains_date(today)`

Editable/deletable ⟺ the session's course's cycle contains today's date. Equivalent to
comparing against `get_active_cycle(today)` (calendar.py:15) given cycles are
non-overlapping, but avoids the extra query and the None-handling of a second lookup.
Strict semantics: when today falls in a gap between cycles, everything is frozen.

- Alternative rejected: "latest cycle by `start_date` stays editable" — pre-creating a
  future cycle would freeze all current sessions prematurely.
- Alternative rejected: storing a `frozen` flag on the session — the rule is
  derived data; a stored flag would go stale the day a new cycle is created.

Helper: add a module-level pure predicate in `src/school/calendar.py` (next to the
other shared helpers), e.g. `session_is_frozen(session) -> bool` using
`timezone.now().date()` — the single source of truth mirroring
`validate_session_date`, so the panel and the API cannot drift apart. It should treat
a missing `school_cycle` as frozen (consistent with creation, which rejects
cycle-less courses).

### D2 — Guard placement: view/API layer, not `clean()`

Cycle-freshness is policy ("is this cycle still active?"), not data validity ("is this
date valid for this course?"). `clean()` keeps its creation-only validation so
`test_existing_session_survives_later_calendar_change` stays true. The three
teacher-facing entry points call the shared predicate directly.

### D3 — Frozen edit UX: alert dialog on the pencil, trash hidden

- Pencil button (frozen): becomes a `c-alert-dialog` trigger — title "Sesión de solo
  lectura", description naming the cycle (`session.course.school_cycle.name` plus its
  date range), single "Entendido" action (the `cancel` component). Reuses the exact
  component already used by the adjacent delete button — no new UI surface.
- Trash button (frozen): simply not rendered. No disabled tease-button, no second
  denial dialog.
- The view computes the flag once into the context (e.g. `session_is_editable`) so the
  template never duplicates rule logic.

### D4 — Frozen POST responses mirror existing failure shapes

- Edit POST (frozen): `messages.error` ("Esta sesión pertenece a un ciclo anterior y
  ya no se puede editar.") + `_render_readonly(request)` — for HTMX, retarget to
  `#attendance-panel` exactly like the invalid-formset path (session_detail.py:70-76);
  the readonly partial already renders messages (template lines 121-127). Non-HTMX:
  redirect to the session detail URL.
- Delete POST (frozen): `messages.error` + the same list-rerender/redirect shapes
  `SessionDeleteView` already uses for success.
- `?edit=1` on a frozen session: silently render read-only (no error message — the
  page itself explains via the dialog button).

### D5 — API rejection: 422 with structured detail

`update_session_records` raises `HttpError(422,
'La sesión pertenece a un ciclo anterior y ya no se puede editar.')` — consistent with
the existing 404 `HttpError` for missing sessions, keeping the response envelope
simple. Ownership scoping stays unchanged (404 for other teachers' sessions).

### D6 — Query: `select_related('course__school_cycle')`

`PreviousSessionDetailView.get_queryset` already select_relateds course fields;
add `course__school_cycle` (and use it in `SessionDeleteView`'s and the API's
session lookup) so the predicate costs no extra query.

## Risks / Trade-offs

- [Frozen rule depends on wall-clock date] → Same class of risk as the existing
  "is it today?" redirects; acceptable, and the strict gap semantics were chosen
  deliberately.
- [API consumers (desktop integration) see a new 422 for old sessions] → The desktop
  integration only reads (`/api/desktop/students`); the PATCH endpoint is only used by
  the today-session page, which cannot be frozen. No real consumer breaks.
- [Duplicated Spanish error strings across panel and API] → Centralize the message
  next to the predicate in `school/calendar.py` so all surfaces share it.

## Open Questions

(none — gap semantics, delete scope, and modal approach were decided during
exploration)
