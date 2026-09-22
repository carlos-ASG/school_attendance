# Design: restrict-sessions-to-scheduled-weekdays

## Context

Session-date validation lives in `src/school/calendar.py` as pure functions (design D5 of `add-school-calendar`), acting as a single funnel: `validate_session_date(course, date)` is called by `TodaySessionCreateView.post`, `SessionForm.clean_date`, and `AttendanceSession.clean` (which covers the Django admin via `full_clean`). The panel UI consumes it through `today_session_block_reason`, which drives the disabled state and reason text of the "Tomar asistencia" button on the course detail page (the template already renders both).

The funnel currently enforces: (1) date inside the course's School Cycle, (2) date not a NonSchoolDay. It ignores `ClassSchedule` (weekday + start/end time per course), so a Monday-only course can get a session on a Tuesday through any entry point.

An active, unarchived change (`add-school-calendar`) modified the same two teacher-panel requirements this change touches; our deltas stack on top of its versions.

## Goals / Non-Goals

**Goals:**

- Block session creation on weekdays the course does not meet, across all entry points, by extending the existing funnel.
- Block session creation entirely for courses with no schedule slots (decision: no schedule = outside working days).
- Preserve creation-time-only semantics (D6): schedule changes never invalidate or block editing of existing sessions.
- Keep suite results independent of the weekday the tests run on.

**Non-Goals:**

- Time-of-day windows (a class's start/end times are not enforced against "now").
- A session format for make-up classes held off-schedule (future change).
- Revalidating or migrating existing sessions; dashboard or admin UI changes.

## Decisions

### D1. Extend `validate_session_date` instead of adding checks at call sites

The calendar module is the declared single source of truth; every entry point already calls it. Adding rule 3 there propagates to the today flow, the backdated form, admin, and the button's disabled state with zero view changes. Alternative (per-view checks) rejected: duplicates logic and lets entry points drift.

**Amendment (implementation finding):** "zero template changes" turned out wrong. The course detail template passed `{% if today_reason %}disabled{% endif %}` inside the `<c-button>` component tag; cotton passes component-tag attribute content through literally (Django never evaluates it), so the disabled attribute never rendered. Fix: the shared `c-button` component gained a server-side boolean `disabled` prop (`c-vars` + conditional render in the button branch), and the usage passes `disabled="{% if today_reason %}true{% endif %}"`. Alpine's `::disabled` binding (used on the today session page) was not applicable — that evaluates client-side state, while `today_reason` is server-side.

### D2. Weekday-only match, times ignored

`date.weekday()` must match at least one `ClassSchedule.weekday` of the course. Times are not enforced because teachers legitimately record attendance after class ends; time windows would add timezone/grace-window complexity for little integrity gain.

### D3. No schedule slots = always blocked

A course without slots can never host a session. Alternative (no schedule = unrestricted) rejected by product decision: schedule-less courses are a data-quality problem to fix in admin, not a hole to allow through. Consequence: teachers of such courses see a permanently disabled button with a clear reason; admins assign schedules (seed data already creates them).

### D4. Error messages and Spanish pluralization

Two new `ValidationError` messages from the funnel:
- No slots: `El curso no tiene horario asignado.`
- Weekday mismatch: `El curso no tiene clase los días {weekday}.` where `{weekday}` is `ClassSchedule.Weekday(value.weekday()).label.lower()`.

The "los días {singular}" phrasing avoids Spanish plural forms ("lunes" never takes -s, "sábado" does) — no pluralization table needed. Labels come from the model's `IntegerChoices`, the same source the schedule UI renders.

### D5. One query, single pass

The check fetches `course.schedule_slots.values_list('weekday', flat=True)` once and tests membership locally, mirroring how `non_school_day` is handled. Cost: one extra query per validation call — these are single-session operations (form posts), not loops. Callers may pre-fetch; `CourseDetailView` already prefetches `schedule_slots`, and Django's queryset cache makes the extra query a no-op there when the relation is prefetched on the instance.

### D6. Test fixtures: `add_full_week_schedule` helper

All existing tests create courses without slots and create sessions on arbitrary weekdays — under D3 they would all break, and single-weekday fixtures would make outcomes depend on the run day. A helper creating one slot per weekday (7 slots) is applied in `make_course_data` and the affected `setUpTestData`s. Targeted mismatch tests instead build a schedule that excludes a computed date's weekday (e.g. all weekdays except the target's).

### D7. Delta stacking on the active `add-school-calendar` change

The teacher-panel delta's `MODIFIED` requirements are based on the `add-school-calendar` versions (latest form), not the older main-spec text. The attendance-tracking delta adds a standalone requirement (schedule validation) rather than modifying `add-school-calendar`'s calendar-validation requirement, avoiding a three-way merge on one requirement. Archive order: `add-school-calendar` first, then this change.

## Risks / Trade-offs

- [Courses without schedules become attendance-dead] → Intended per D3; mitigated by the explicit "sin horario" message naming the fix (admin assigns schedule) and by seed data already creating slots.
- [Direct `AttendanceSession.objects.create()` bypasses `clean()` and the rule] → Pre-existing design: all user-facing entry points pre-validate through the funnel; direct ORM writes remain trusted code paths (seed, tests).
- [Stacked deltas diverge if `add-school-calendar` is reworked before archiving] → Its requirement text for the two shared requirements must be re-based here; tracked as an archive-order note (D7).
- [Off-schedule make-up classes become unrecordable] → Accepted for now; explicitly a separate future format (Non-Goals).
