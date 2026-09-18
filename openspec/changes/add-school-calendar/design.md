# Design: add-school-calendar

## Context

The attendance domain (`src/school/models.py`) has Students, Teachers, Subjects, Student Groups, Courses (with weekly `ClassSchedule` slots), `AttendanceSession`, and `AttendanceRecord`. Session date validation today is only "not in the future" (`AttendanceSession.clean()`, also mirrored in `SessionForm`). There are three session-creation entry points: the today flow (`TodaySessionCreateView`, which calls `objects.create()` directly and bypasses `full_clean()`), the history form (`SessionForm` + `CourseSessionHistoryView.post`), and the Django admin. The database is SQLite, disposable (dev-only, reseeded via `seed_dev_data`). There is no `School` entity: one deployment = one school.

## Goals / Non-Goals

**Goals:**

- Model the school cycle (name, type, start/end) and its non-school days (single days and vacation ranges).
- Anchor every Course to exactly one cycle; make course uniqueness per-cycle.
- Validate session creation against the course's cycle (window + non-school days) at every entry point.
- Teacher panel UX that reflects the calendar (banner, disabled today-card, readable form errors).

**Non-Goals:**

- No `School` entity / multi-tenancy.
- No SEP templates, no bulk group operations (queued changes).
- No expected-sessions reporting; no weekend validation; no retroactive session invalidation.

## Decisions

### D1: The course's own cycle is the validation context (no global "active cycle" lookup)

A session date is validated against `session.course.ciclo`. With Course→Cycle mandatory, every session has an unambiguous window; a course from "Agosto – Diciembre 2026" can never have sessions in January even after the next cycle starts. A "cycle containing today" lookup was rejected: it couples validation to the current date and becomes ambiguous if cycles ever overlap. A module-level helper `get_active_cycle(date)` (the single cycle containing that date) is still useful for dashboard scoping, but not for validation.

### D2: One cycle at a time; no-overlap validated in `clean()`

Schools run a single cycle model; overlapping cycles are out of scope. Cross-row rules cannot be DB `CheckConstraint`s in SQLite, so no-overlap lives in `Model.clean()` (runs via admin forms and `full_clean()`). Adjacent cycles and gaps between cycles (summer) are allowed — during a gap, no course's cycle contains the date, so no sessions can be created, which is correct.

### D3: One `NonSchoolDay` table with a nullable end date

`fecha_fin = NULL` means a single day (20-nov); a range means a vacation period. Two tables (`Holiday` + `VacationPeriod`) were rejected: duplicated validation, admin, and queries for the same semantics. A mandatory end with `start == end` was rejected as redundant data. Overlapping non-school days are allowed without validation (union semantics, less capture friction).

### D4: Generous per-type duration bounds (constants in the model)

| Type | Bounds | Rationale |
|---|---|---|
| ANNUAL | 240–400 days | SEP-style cycle ≈ 341 days; rejects "annual Feb–Apr" absurdity |
| SEMESTRAL | 110–240 days | Real Ago–Dic semester ≈ 116 days |
| QUATRIMESTRAL | 85–145 days | Real cuatrimestre ≈ 103 days |

Real semesters and cuatrimestres overlap in calendar length (the difference is pedagogical), so ranges intentionally overlap; the type guards against absurd durations, it does not strictly classify. Disjoint ranges were rejected: short real semesters (~116 days) would be rejected as "semestral". Bounds are named module-level constants, trivially adjustable. Validated in `clean()`.

### D5: A shared calendar helper module (`src/school/calendar.py`)

Pure functions, no new app:

- `get_active_cycle(date)` → the `SchoolCycle` containing the date or `None`
- `get_non_school_day(cycle, date)` → the matching `NonSchoolDay` or `None`
- `validate_session_date(course, date)` → raises `ValidationError` with user-readable Spanish messages ("La fecha está fuera del ciclo …", "El {fecha} es inhábil: {nombre}")

Rationale: `AttendanceSession.clean()` only runs via `full_clean()`, and the today flow calls `objects.create()` directly. The helper is the single source of truth for the rule and its messages; `AttendanceSession.clean()`, `SessionForm.clean_date()`, `TodaySessionCreateView.post()`, and the admin all call it. This mirrors how the existing future-date rule already lives in both model and form.

### D6: Creation-time-only validation

Sessions are historical truth. Marking a recorded day as inhábil later never invalidates, locks, or deletes existing sessions (consistent with the reporting semantics: the day simply does not count). No admin override flag for "class actually happened" — if it did, the calendar entry is wrong and the admin fixes it; error messages name the offending entry so the fix is discoverable.

### D7: `Course.ciclo` — FK PROTECT, mandatory; uniqueness per cycle

`on_delete=PROTECT` matches the existing style (teacher/subject/group are PROTECT): deleting a cycle with courses is blocked; deleting a childless cycle cascades its non-school days. The unique constraint `(teacher, subject, student_group)` becomes `(teacher, subject, student_group, ciclo)` because the same trio legitimately repeats across cycles (group retakes the subject next cuatrimestre, course replicated yearly).

### D8: Dashboard UX — cycle-scoped main list, "Otros ciclos" section, banner

- Main list: the teacher's courses whose cycle contains today. Alternatives rejected: listing all courses forever (clutter once cycles accumulate) and hiding other-cycle courses entirely (loses access to their history pages).
- Secondary "Otros ciclos" section: past/future-cycle courses with their cycle name, linking to course detail (history stays reachable; no "Sesión de hoy" card there).
- Banner when today is not a class day: "Hoy no hay clases — {nombre del inhábil}" for non-school days, or a no-active-cycle notice when no cycle contains today.
- "Sesión de hoy" card: disabled with a visible reason on non-school days or out-of-cycle days. `TodaySessionCreateView` still validates server-side (defense in depth; POST-only endpoint must stay safe).

### D9: Conventions

`SchoolCycle` / `NonSchoolDay` with Spanish verbose names ('Ciclo escolar', 'Día inhábil'), `TextChoices` for types, `CheckConstraint` start-before-end on both models (mirroring `classschedule_start_before_end`), unfold admin with a `NonSchoolDay` `TabularInline` inside `SchoolCycleAdmin`; `CourseAdmin` gains the cycle in fields/list_filter. All user-visible copy in Spanish; identifiers in English.

## Risks / Trade-offs

- [Cross-row validation in `clean()` can be bypassed by raw `.create()`] → every session-creation entry point calls the shared helper; tests pin the panel form, the today flow, and the admin.
- [Admin marks a day inhábil that actually had class → teacher blocked] → error message names the offending non-school day; admin fixes the calendar and the teacher retries.
- [Duration constants may not fit an edge school] → generous overlapping bounds; named constants, trivially adjustable.
- [Wiping the DB loses manually entered dev data] → accepted (dev-only); the updated seeder regenerates everything.
- ["Otros ciclos" section grows unbounded over years] → acceptable for v1; a cycle picker can be added later.

## Migration Plan

The database is disposable — no data migration:

1. Delete `db.sqlite3`.
2. `makemigrations school`: CreateModel `SchoolCycle` + `NonSchoolDay`; `AddField course.ciclo` (`null=True`) followed by `AlterField` to `null=False` (valid on empty tables); replace the course unique constraint with the per-cycle one.
3. `migrate`, then update `seed_dev_data`: demo `SEMESTRAL` cycle "Agosto – Diciembre 2026" spanning today, a 20-nov asueto, a Christmas vacation range, and all seeded courses assigned to it.

Rollback: restore a backup of `db.sqlite3` (dev only).

## Open Questions

None blocking. Tunable at implementation: exact duration constants, demo seed dates, banner copy.
