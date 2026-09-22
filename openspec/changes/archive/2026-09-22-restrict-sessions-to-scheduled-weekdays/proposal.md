# Proposal: restrict-sessions-to-scheduled-weekdays

## Why

The "Tomar asistencia" control on the course detail page can create an attendance session on any date, even when the course does not meet that weekday (per its `ClassSchedule` slots). This lets teachers record sessions on days the class never happens, corrupting attendance statistics. The calendar validation funnel (`validate_session_date`) already enforces cycle containment and non-school days, but knows nothing about weekly schedules.

## What Changes

- Extend `validate_session_date` in `src/school/calendar.py` with a third rule: a session date is only valid when the course has schedule slots AND at least one slot's weekday matches the date's weekday.
- Courses with **no** schedule slots are treated as never in session: all session creation is blocked for them.
- Strict scope: the rule applies to every creation entry point — today flow ("Tomar asistencia"), backdated sessions ("Crear sesión en otra fecha" form), and Django admin (via `AttendanceSession.clean`).
- Creation-time-only (consistent with design D6): existing sessions stay valid even if schedules change afterwards.
- Weekday-only: start/end times are ignored — no time-of-day enforcement.
- The course detail button's disabled state and reason text inherit automatically through `today_session_block_reason`; no template or view changes.
- Test fixtures updated: courses used in tests get full-week schedules so suite results never depend on the weekday the suite runs.

## Non-goals

- Time-of-day windows (blocking outside a class's hours) — deliberately out of scope.
- Make-up classes held off-schedule: they need their own session format, a separate future change.
- Any dashboard changes (the dashboard has no session-creation control).
- Schedule management UI (schedules continue to be admin-managed).
- Backfilling or revalidating existing sessions.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `attendance-tracking`: new requirement — attendance session schedule validation (weekday match against the course's `ClassSchedule` slots; no-schedule courses blocked; creation-time-only; Spanish errors naming the weekday).
- `teacher-panel`: the "Create today session shortcut" and "Session creation from the panel" requirements gain schedule-weekday rejection scenarios (control disabled with reason; backdated form rejects non-scheduled weekdays).

## Impact

- **Code**: `src/school/calendar.py` (rule + docstring), `src/school/models/attendance_session.py` (docstring only). Views, forms, admin, and templates unchanged — they already delegate to the shared funnel.
- **Tests**: `src/school/tests.py` (helper `add_full_week_schedule`, new calendar/model cases), `src/teacher_panel/tests.py` (fixtures + new view tests).
- **Dependencies**: stacks on the active `add-school-calendar` change (it modified the same two teacher-panel requirements); archive it before this change.
- **Ops**: courses without schedules can no longer take attendance — admins must assign schedules (seed data already does). No migration, no schema change.
