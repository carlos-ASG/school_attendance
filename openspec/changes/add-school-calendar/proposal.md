## Why

The system treats every past date as a valid attendance day. Mexican schools run distinct school cycles (annual, semester, or cuatrimestral) with cycle-specific non-working days — single holidays (e.g. November 20) and vacation ranges (Christmas, Holy Week, summer) — and each school configures its own calendar. Without a calendar, sessions can be recorded on non-class days and courses have no cycle context.

## What Changes

- New `SchoolCycle` model: name (e.g. "Agosto – Diciembre 2026"), type (`ANNUAL` / `SEMESTRAL` / `QUATRIMESTRAL`), start and end dates. Validation: start before end, duration within generous per-type bounds, and no overlap with any other cycle (one cycle at a time per school).
- New `NonSchoolDay` model: name, type (`ASUETO` / `VACACIONES` / `OTRO`), start date, and optional end date — a NULL end date means a single day; a range means a vacation period. Belongs to a `SchoolCycle` and is validated to fall inside the cycle's bounds. Overlapping non-school days are allowed (harmless union).
- **BREAKING**: `Course` gains a mandatory FK to `SchoolCycle` (PROTECT) and course uniqueness becomes `(teacher, subject, student_group, cycle)`. The dev database is disposable: it will be wiped, the seeder updated, and data regenerated.
- Attendance session creation is validated against the course's cycle: the date must fall inside the cycle and must not be a non-school day. Validation applies at creation time only — via teacher panel, Django admin, or programmatic paths — and existing sessions are never retroactively invalidated when the calendar changes.
- Teacher panel UX: the dashboard lists the current cycle's courses and shows a "Hoy no hay clases — {reason}" banner on non-school days or days outside any cycle; the create-past-session form rejects non-school-day and out-of-cycle dates with readable Spanish errors; the "Sesión de hoy" flow rejects today when it is a non-school day or outside the cycle.
- Django admin: `SchoolCycle` admin with a `NonSchoolDay` inline; `Course` admin gains the cycle field.
- `seed_dev_data` grows a demo cycle with demo non-school days.

## Non-goals

- No `School` entity or multi-tenancy (one deployment = one school).
- No SEP template loading (queued change: `add-sep-calendar-templates`).
- No bulk group membership operations (queued change: `add-group-management`).
- No "expected sessions" reporting — attendance percentages keep using recorded sessions as the denominator.
- No weekend validation — course schedules already constrain class days.
- No retroactive invalidation of sessions when the calendar changes later.

## Capabilities

### New Capabilities
- `school-calendar`: school cycle and non-school day definition, entity validation, and admin management.

### Modified Capabilities
- `academic-structure`: Course composition gains a mandatory school cycle; course uniqueness becomes per-cycle.
- `attendance-tracking`: session creation gains cycle-window and non-school-day validation (creation-time only).
- `teacher-panel`: dashboard cycle scoping, non-school-day banner, and calendar-aware form errors.

## Impact

- `src/school/`: models, migrations, admin, seeder, tests.
- `src/teachers/`: dashboard, today-session, and session-history views/forms; templates; tests.
- Database: wiped and reseeded from the updated seeder.
