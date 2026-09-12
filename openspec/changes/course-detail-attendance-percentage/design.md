## Context

The teacher panel's course detail page (`teachers/course_detail.html`) currently renders the course's student group as a plain unordered list. Attendance data already exists in the `AttendanceSession` and `AttendanceRecord` models, but it is not summarized anywhere in the teacher UI. The `CourseDetailView` prefetches students and schedule slots but does not aggregate attendance records.

This design covers two related changes:
1. Surfacing a per-student attendance percentage on the course detail page.
2. Preventing attendance sessions from being created for future dates, because attendance cannot be taken before a class occurs.

## Goals / Non-Goals

**Goals:**
- Display each student's attendance as `attended/total (percentage%)` in a table on the course detail page.
- Count `PRESENT`, `LATE`, and `EXCUSED` as attended.
- Compute the values efficiently in the view using ORM aggregation, avoiding N+1 queries.
- Reject future dates when saving an `AttendanceSession`, regardless of whether the save originates from the teacher panel or the Django admin.
- Keep all teacher-facing text in Spanish.

**Non-Goals:**
- HTMX live update of the attendance table after session creation/deletion.
- Removing session management from the Django admin.
- Adding sorting, filtering, searching, or export to the student table.
- Changing attendance statuses or their definitions.

## Decisions

### Calculate attendance in the view, not in the model or template
A model method on `Student` would need a `course` argument and would issue queries from the template, making N+1 bugs likely. Template math is hard to test and tends to duplicate business logic. Computing a lookup dict in `CourseDetailView.get_context_data()` keeps the logic testable and lets us issue exactly two aggregation queries (total sessions and attended counts per student).

### Denominator is total sessions for the course
Using the count of all `AttendanceSession` records for the course is simple and stable. It matches the user's expectation that each session represents one attendance opportunity. Students who join the group after some sessions have passed will naturally have lower percentages until they catch up; this is acceptable because retroactive record creation is out of scope.

### Show `0%` when no sessions exist
When the denominator is zero, the percentage is `0/0 (0%)`. This avoids division-by-zero complexity in the template and clearly communicates that no attendance has been recorded yet.

### Validate future dates at the model level
Placing the validation in `AttendanceSession.clean()` ensures it applies uniformly to the teacher panel form, the Django admin, and any programmatic saves. Adding the same check to `SessionForm` would be redundant if the form calls `full_clean()`, but a form-level check can provide a friendlier error message location. For this change, model-level validation is sufficient because both `SessionForm` and the admin already invoke model validation.

### Keep HTMX behavior unchanged
The session creation/edit/delete panel remains an HTMX partial. The student attendance table lives in the main template and updates only on full page reload. This keeps the change small and avoids restructuring the existing partial hierarchy.

## Risks / Trade-offs

- **[Risk]** A course with many students and many sessions could make the aggregation query slower over time.  
  **Mitigation:** The query filters by `session__course` and groups by `student_id`; an index already exists on `AttendanceRecord.session` via the foreign key, and `AttendanceSession.course` is a foreign key. If performance becomes an issue later, add a composite index on `(session__course, student, status)`.

- **[Risk]** Students added to the group after sessions exist will show `0/N` until new sessions are created, which may look like poor attendance.  
  **Mitigation:** This is an existing data-model behavior (records are created at session creation, not retroactively). The UI is correctly reflecting the data. Out of scope for this change.

- **[Risk]** The future-date validator could break admin workflows if admins currently create sessions in advance.  
  **Mitigation:** This is intentional per the requirement. The validator applies to everyone; if an admin needs an exception later, that should be a separate, explicit capability.

- **[Risk]** Spanish translations for new labels must be consistent with the rest of the panel.  
  **Mitigation:** Hard-code Spanish strings in the template, matching existing labels like "Estudiantes".

## Migration Plan

No database migration is required. The validation change is behavioral only. Deploy by running the existing test/verification commands and confirming `uv run manage.py check` passes.

## Open Questions

None.
