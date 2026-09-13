## 1. Model validation

- [x] 1.1 Add `clean()` to `AttendanceSession` in `src/school/models.py` to reject dates later than `timezone.now().date()`.
- [x] 1.2 Update existing `AttendanceSession` tests in `src/school/tests.py` (or add new ones) to verify a future date raises `ValidationError` and today/past dates are accepted.

## 2. View aggregation

- [x] 2.1 Update `CourseDetailView.get_context_data()` in `src/teachers/views.py` to compute total sessions and a per-student attended count, then build a lookup dict for the template.
- [x] 2.2 Ensure the aggregation query filters by the current course and counts only `PRESENT`, `LATE`, and `EXCUSED` statuses.
- [x] 2.3 Add/update tests for `CourseDetailView` verifying that the attendance context contains the expected `attended/total/percentage` values for students.

## 3. Template update

- [x] 3.1 Replace the student `<ul>` in `src/teachers/templates/teachers/course_detail.html` with a `<table>` containing "Estudiante" and "Asistencia" columns.
- [x] 3.2 Render each row using the attendance lookup dict; display `0/0 (0%)` when no sessions exist and format the percentage to one decimal place.

## 4. Verification

- [x] 4.1 Run `uv run manage.py check` and confirm no errors.
- [x] 4.2 Run the test suite (or relevant tests) and confirm all pass.
- [x] 4.3 Manually verify the course detail page renders the attendance table correctly and the session form rejects future dates.

## 5. Create today button

- [x] 5.1 Add `create_today` handling to `CourseDetailView.post()`: create a session for today (or reuse the existing one) and redirect to its detail view; expose `today_session` in the context.
- [x] 5.2 Add the "Crear sesión de hoy" button/link to `session_panel.html`, keeping the date picker form alongside.
- [x] 5.3 Add tests for one-click today-session creation, duplicate handling, and template rendering.
