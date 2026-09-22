# Tasks: restrict-sessions-to-scheduled-weekdays

## 1. Validation rule (funnel)

- [x] 1.1 Given a course with schedule slots, when `validate_session_date` is called with a date whose weekday matches a slot (and passes cycle/non-school-day checks), then no error is raised; and when the weekday matches no slot, then it raises `ValidationError` with `El curso no tiene clase los días {weekday}.` using `ClassSchedule.Weekday(...).label.lower()` — extend `src/school/calendar.py` and update its module/`validate_session_date` docstrings
- [x] 1.2 Given a course with no schedule slots, when `validate_session_date` is called with any in-cycle date, then it raises `ValidationError` with `El curso no tiene horario asignado.` (single `values_list('weekday', flat=True)` query, membership test in Python)
- [x] 1.3 Update the `AttendanceSession.clean` docstring to mention the weekday rule; verify via `uv run manage.py check` that no wiring changes are needed (today flow, `SessionForm`, admin all inherit)

## 2. Test fixtures

- [x] 2.1 Add `add_full_week_schedule(course)` helper in `src/school/tests.py` (one slot per weekday, e.g. 07:00–08:00) and apply it inside `make_course_data`
- [x] 2.2 Apply the helper in the `setUpTestData` of every `src/teacher_panel/tests.py` class whose courses create sessions through validated paths (`TodaySessionCreateViewTests`, `CourseSessionHistoryViewTests`, `TodaySessionDetailViewTests`, session URL/edit/delete classes)
- [x] 2.3 Run `uv run manage.py test` and confirm the full suite passes without weekday-dependent failures

## 3. Calendar/model tests (`src/school/tests.py`)

- [x] 3.1 Calendar helper tests: scheduled weekday allowed; non-scheduled weekday rejected (error names the weekday); no-schedule course rejected for any in-cycle date
- [x] 3.2 `AttendanceSessionCleanTests`: `full_clean` rejected on a non-scheduled weekday and for a no-schedule course; existing session stays valid after its schedule slot is removed (creation-time-only, D6)

## 4. Panel tests (`src/teacher_panel/tests.py`)

- [x] 4.1 Today flow: POST to `today_session_create` blocked when today's weekday matches no slot (course scheduled for all weekdays except today's) — no session created, redirect back to course detail, message contains "no tiene clase"
- [x] 4.2 Today flow: POST blocked for a course with no schedule — no session created, message contains "sin horario" / "no tiene horario"
- [x] 4.3 History form: backdated in-cycle date on a non-scheduled weekday rejected — form re-renders with weekday error (plain + HTMX fragment)
- [x] 4.4 Course detail page: "Tomar asistencia" button renders disabled with reason for a no-schedule course and for a wrong-weekday day (context `today_reason`)

## 5. Verification

- [x] 5.1 `uv run manage.py check` passes; full `uv run manage.py test` suite green (including admin/session/model suites)
- [x] 5.2 Manual smoke via `uv run manage.py runserver`: unscheduled course's button disabled with reason; scheduled course on wrong weekday disabled; correct weekday creates session

## 6. Button disabled rendering (defect fix)

- [x] 6.1 Root cause: `{% if today_reason %}disabled{% endif %}` inside the `<c-button>` component tag passed through cotton as literal text (Django never evaluates component-tag attribute content), so the rendered button never had a `disabled` attribute; earlier `assertContains(response, 'disabled')` assertions false-positived on Tailwind `disabled:*` classes
- [x] 6.2 Add server-side boolean `disabled` prop to the cotton button component (`c-vars` + `{% if disabled %} disabled{% endif %}` in the button branch) and pass `disabled="{% if today_reason %}true{% endif %}"` in `course_detail.html`; verify rendered `<button disabled ... type="submit">` appears for blocked cases and is absent otherwise
- [x] 6.3 Harden the three disabled-scenario tests in `CourseDetailViewTests` to assert the real markup (`<button disabled ... type="submit">` within the today form) via `assertRegex`
- [x] 6.4 Fix template copy: "Sesioses" → "Sesiones", "Sin horario asignar." → "Sin horario asignado."
