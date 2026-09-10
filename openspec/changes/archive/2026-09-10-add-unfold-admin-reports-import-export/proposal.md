## Why

The project currently uses the default Django admin for staff and superusers. It works, but it is plain and does not surface attendance insights or provide a way to bulk-load the student roster that schools typically already have in spreadsheets. Adding django-unfold will modernize the admin experience, a dedicated Reports page will give staff a quick visual summary of attendance, and django-import-export will let them import and export the student roster without writing code.

## What Changes

- Add `django-unfold` as the admin theme.
- Convert existing `ModelAdmin` and inline classes to Unfold equivalents.
- Add a custom "Reports" admin page reachable from the sidebar, showing:
  - Summary cards (student count, classroom count, recent sessions).
  - Attendance-by-status pie chart.
  - Daily attendance trend line chart.
  - Attendance-by-classroom bar chart.
- Add `django-import-export` integration with Unfold styling on the `Student` admin, supporting CSV and XLSX import/export, including mapping to `StudentGroup` by name.
- Keep the existing `/panel/` teacher interface unchanged.

## Capabilities

### New Capabilities

- `admin-theme`: Apply django-unfold to the Django admin, including Unfold `ModelAdmin`, inlines, and sidebar configuration.
- `admin-reports`: Add a staff-only Reports page inside the admin with summary metrics and Chart.js bar, line, and pie charts.
- `student-import-export`: Import and export the `Student` roster (with `StudentGroup` mapping) from CSV/XLSX inside the Unfold admin.

### Modified Capabilities

- None. This change does not alter the existing domain requirements for academic structure, attendance tracking, or the teacher panel.

## Impact

- Dependencies: adds `django-unfold`, `django-import-export`, and an XLSX backend (`openpyxl` / `tablib[xlsx]`).
- Affected files: `pyproject.toml`, `src/config/settings.py`, `src/school/admin.py`, new `src/school/resources.py`, new `src/school/components.py`, new `src/school/templates/admin/...`.
- User model: no custom user model changes are required for this change, but the project may later introduce one for migration safety if desired.

## Non-goals

- Changing the `/panel/` teacher-facing interface.
- Import/export for teachers, subjects, classrooms, schedules, or attendance records.
- Real-time analytics, notifications, or advanced reporting beyond the three chart types listed.
- Replacing the existing authentication or permission system.
