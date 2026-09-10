## 1. Dependencies and settings

- [x] 1.1 Given the project uses `uv`, when I add `django-unfold`, `django-import-export`, and `openpyxl` to `pyproject.toml`, then `uv lock && uv sync` succeeds.
- [x] 1.2 Given `django-unfold` is installed, when I add `unfold`, `unfold.contrib.filters`, `unfold.contrib.forms`, `unfold.contrib.inlines`, and `unfold.contrib.import_export` before `django.contrib.admin` in `INSTALLED_APPS`, then `uv run manage.py check` passes.
- [x] 1.3 Given Unfold is enabled, when I configure a minimal `UNFOLD` dictionary with site title, sidebar navigation, and the Reports link, then the admin renders with the new branding.

## 2. Admin theme migration

- [x] 2.1 Given the existing `school/admin.py`, when I make all `ModelAdmin` classes inherit from `unfold.admin.ModelAdmin` and all inlines inherit from `unfold.admin.TabularInline`, then all existing admin pages load without errors.
- [x] 2.2 Given the converted admin classes, when I open the Student, Teacher, Subject, StudentGroup, Classroom, ClassSchedule, AttendanceSession, and AttendanceRecord changelists, then they use Unfold styling and filters.
- [x] 2.3 Given the converted admin classes, when I open a Classroom or AttendanceSession change form, then the `ClassSchedule` and `AttendanceRecord` inlines render with Unfold inline styling.

## 3. Student import/export

- [x] 3.1 Given the import/export requirement, when I create `src/school/resources.py` with a `StudentResource` that maps `id`, `first_name`, `paternal_surname`, `maternal_surname` (required), `email`, and `student_groups` (comma-separated group names, Spanish headers), then the resource validates cleanly.
- [x] 3.2 Given the `StudentResource` exists, when I update `StudentAdmin` to inherit from `ImportExportModelAdmin` and use `unfold.contrib.import_export.forms.ImportForm` and `ExportForm`, then import and export buttons appear on the Student changelist.
- [x] 3.3 Given the import form is enabled, when I upload a valid XLSX file with existing group names, then the preview shows the rows and confirmation creates the students with correct group associations.
- [x] 3.4 Given the import form is enabled, when I upload a file with a non-existent group name, then the preview shows a validation error and refuses to import.
- [x] 3.5 Given the export form is enabled, when I export students to CSV, then the file contains `id`, `Nombre`, `Apellido paterno`, `Apellido materno`, `Correo electrónico`, and `Grupos` columns.

## 4. Reports page

- [x] 4.1 Given the Reports page requirement, when I create a custom view using `UnfoldModelAdminViewMixin` attached to `AttendanceSessionAdmin.get_urls()`, then `/admin/school/attendancesession/reports/` returns a page inside the Unfold layout.
- [x] 4.2 Given the Reports view exists, when I add the Reports entry to `UNFOLD["SIDEBAR"]["navigation"]`, then staff users see the link in the sidebar.
- [x] 4.3 Given a staff user opens the Reports page, when the default date range is used, then summary cards show total students, total classrooms, and session count for the last 30 days.
- [x] 4.4 Given a staff user opens the Reports page, when the data is loaded, then a pie chart shows attendance status distribution using Chart.js.
- [x] 4.5 Given a staff user opens the Reports page, when the data is loaded, then a line chart shows daily attendance counts by status.
- [x] 4.6 Given a staff user opens the Reports page, when the data is loaded, then a bar chart shows attendance counts grouped by classroom.
- [x] 4.7 Given the Reports page has a date filter, when a staff user selects a custom range and submits, then all metrics and charts update to reflect the selected range.

## 5. Verification and cleanup

- [x] 5.1 Given all changes are in place, when I run `uv run manage.py check`, then no errors or warnings are reported.
- [x] 5.2 Given the `/panel/` teacher interface, when a teacher logs in and navigates to `/panel/`, then the page renders with the existing project templates and is unaffected by Unfold.
- [x] 5.3 Given the Reports page requires staff access, when a non-staff user accesses the URL directly, then the system returns a 403 or redirects to login.
- [x] 5.4 Given the Student import/export requires staff access, when a non-staff user accesses the import URL directly, then the system denies access.
