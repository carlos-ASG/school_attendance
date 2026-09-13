## Why

Teachers currently see only a plain list of students on the course detail page. To quickly identify at-risk students and track group attendance health, the page should surface each student's attendance rate directly alongside their name. Additionally, sessions should not be created for future dates, because attendance cannot be recorded before a class has actually occurred.

## What Changes

- Replace the student list on `teachers/course_detail.html` with a table showing each student's attendance summary.
- Add an attendance percentage column formatted as `attended/total (percentage%)`, e.g. `14/16 (87.5%)`.
- Count as attended any record whose status is `PRESENT`, `LATE`, or `EXCUSED`.
- Use the total number of sessions created for the course as the denominator; show `0%` when no sessions exist.
- Compute the values in `CourseDetailView` using an ORM aggregation with prefetching to avoid N+1 queries.
- Add model-level validation so `AttendanceSession` cannot be saved with a date in the future. This applies to both the teacher panel and the Django admin.
- Keep the existing HTMX behavior simple: the student table updates on a full page reload; live sync after in-place session creation is not required.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `teacher-panel`: The course detail view now displays a per-student attendance percentage table and computes attendance summaries in the view.
- `attendance-tracking`: Attendance sessions are validated to reject future dates, regardless of where the session is created.

## Impact

- `src/teachers/views.py`: `CourseDetailView` gains attendance aggregation logic.
- `src/teachers/templates/teachers/course_detail.html`: Student list becomes a table with an attendance column.
- `src/school/models.py`: `AttendanceSession.clean()` adds a future-date validator.
- Teacher-facing strings remain in Spanish per existing convention.

## Non-goals

- Real-time update of the attendance table via HTMX when sessions are created or deleted.
- Removing session management from the Django admin.
- Changing the set of attendance statuses or their meanings.
- Adding sorting, filtering, or export of the attendance table.
