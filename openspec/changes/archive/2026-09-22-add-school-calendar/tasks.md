## 1. Models and calendar helper

- [x] 1.1 Create `SchoolCycle` model (name, type `ANNUAL/SEMESTRAL/QUATRIMESTRAL` TextChoices, start/end dates; Spanish verbose names; `CheckConstraint` start < end; module-level duration constants ANNUAL 240–400 / SEMESTRAL 110–240 / QUATRIMESTRAL 85–145 days). Given a cycle, when `full_clean()` runs with an out-of-bounds duration or start >= end, then validation errors are raised.
- [x] 1.2 Add `SchoolCycle.clean()` no-overlap validation (reject ranges overlapping any other cycle; adjacent and gapped cycles allowed). Given an existing cycle, when a new overlapping cycle is full-cleaned, then a `ValidationError` names the conflict.
- [x] 1.3 Create `NonSchoolDay` model (cycle FK CASCADE, name, type `ASUETO/VACACIONES/OTRO`, start date, nullable end date; `CheckConstraint` end is NULL or >= start; `clean()` validates the day/range falls inside its cycle bounds; overlapping entries allowed). Given a range extending past the cycle, when `full_clean()` runs, then a `ValidationError` is raised.
- [x] 1.4 Add mandatory `Course.school_cycle` FK (`PROTECT`) and replace the unique constraint with `(teacher, subject, student_group, school_cycle)`. Generate migrations (`AddField` nullable + `AlterField` not-null, valid on the empty dev DB). Given the same teacher/subject/group in two cycles, when saving, then both courses are allowed; duplicates within one cycle are rejected.
- [x] 1.5 Create `src/school/calendar.py` with `get_active_cycle(date)`, `get_non_school_day(cycle, date)`, and `validate_session_date(course, date)` raising readable Spanish `ValidationError`s ("La fecha está fuera del ciclo …", "El {fecha} es inhábil: {nombre}"). Given a course, when validating an in-cycle non-holiday date, then no error is raised; inhábil and out-of-cycle dates raise naming the offending entry.

## 2. Session validation wiring

- [x] 2.1 Call `validate_session_date` from `AttendanceSession.clean()` and add model tests (out-of-cycle rejected, non-school day rejected, valid date allowed, existing sessions untouched by later calendar changes).
- [x] 2.2 Add calendar checks to `SessionForm.clean_date()` (course cycle context) with form tests: Given an inhábil past date, when the teacher submits the history create form, then the form re-renders with the error naming the non-school day (HTMX fragment included).
- [x] 2.3 Guard `TodaySessionCreateView.post()` with `validate_session_date`: Given today is a non-school day or outside the course's cycle, when the teacher POSTs, then no session is created and a Spanish message explains why.

## 3. Django admin

- [x] 3.1 Register `SchoolCycleAdmin` (unfold) with a `NonSchoolDay` `TabularInline`; add the cycle field/filter to `CourseAdmin`. Given a cycle with courses, when an Admin deletes it, then the deletion is blocked; a childless cycle delete removes its non-school days.
- [x] 3.2 Add admin tests for inline non-school-day management and the blocked cycle deletion.

## 4. Teacher panel UX

- [x] 4.1 Scope the dashboard main list to courses whose cycle contains today, and add the "Otros ciclos" section (cycle name, link to course detail, no today-card). Tests: current-cycle only in main list; other-cycle courses listed separately.
- [x] 4.2 Add the dashboard banner: "Hoy no hay clases — {nombre}" on non-school days, no-cycle notice when no cycle contains today, absent on normal days. Tests for all three states.
- [x] 4.3 Disable the "Sesión de hoy" card button (dashboard and course detail) with a visible reason on non-school or out-of-cycle days; run `uv run manage.py tailwind build` for any new utility classes. Test: the disabled card renders the reason.
- [x] 4.4 Ensure the course detail page's history link and summaries still work for other-cycle courses (navigation not lost).

## 5. Data and verification

- [x] 5.1 Extend `seed_dev_data`: create a demo SEMESTRAL cycle "Agosto – Diciembre 2026" spanning today, a 20-nov asueto, a Christmas vacation range, and assign all seeded courses to it.
- [x] 5.2 Wipe `db.sqlite3`, run `uv run manage.py migrate` and `seed_dev_data`, then `uv run manage.py check` and the full test suite (`uv run manage.py test`).
- [x] 5.3 Manual smoke: dashboard on a normal day, on an inhábil day (banner + disabled card), history form with an inhábil date, admin cycle page with inline days.
