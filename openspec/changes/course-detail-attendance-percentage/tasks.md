## 1. Model validation

- [ ] 1.1 Add `clean()` to `AttendanceSession` in `src/school/models.py` to reject dates later than `timezone.now().date()`.
- [ ] 1.2 Update existing `AttendanceSession` tests in `src/school/tests.py` (or add new ones) to verify a future date raises `ValidationError` and today/past dates are accepted.

## 2. View aggregation

- [ ] 2.1 Update `CourseDetailView.get_context_data()` in `src/teachers/views.py` to compute total sessions and a per-student attended count, then build a lookup dict for the template.
- [ ] 2.2 Ensure the aggregation query filters by the current course and counts only `PRESENT`, `LATE`, and `EXCUSED` statuses.
- [ ] 2.3 Add/update tests for `CourseDetailView` verifying that the attendance context contains the expected `attended/total/percentage` values for students.

## 3. Template update

- [ ] 3.1 Replace the student `<ul>` in `src/teachers/templates/teachers/course_detail.html` with a `<table>` containing "Estudiante" and "Asistencia" columns.
- [ ] 3.2 Render each row using the attendance lookup dict; display `0/0 (0%)` when no sessions exist and format the percentage to one decimal place.

## 4. Verification

- [ ] 4.1 Run `uv run manage.py check` and confirm no errors.
- [ ] 4.2 Run the test suite (or relevant tests) and confirm all pass.
- [ ] 4.3 Manually verify the course detail page renders the attendance table correctly and the session form rejects future dates.
