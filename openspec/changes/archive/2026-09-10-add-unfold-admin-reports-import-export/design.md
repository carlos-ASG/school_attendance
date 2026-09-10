## Context

`school_attendance` uses Django 6.1.1 with SQLite. Staff and superusers sign in through the default Django admin at `/admin/`. Teachers use a separate `/panel/` interface. The admin is functional but visually default, offers no operational overview, and has no bulk-data path for the student roster that schools typically maintain in spreadsheets.

The codebase already defines `Student`, `Teacher`, `Subject`, `StudentGroup`, `Classroom`, `ClassSchedule`, `AttendanceSession`, and `AttendanceRecord`, plus admin classes in `src/school/admin.py`. The project is managed with `uv` and uses `uv run manage.py`.

## Goals / Non-Goals

**Goals:**

- Modernize the Django admin with `django-unfold` while preserving all existing admin behavior.
- Add a staff-only "Reports" page inside the admin that shows attendance summary metrics and bar, line, and pie charts.
- Add CSV/XLSX import and export for `Student` records, including mapping to `StudentGroup` by group name.
- Keep the `/panel/` teacher interface completely untouched.

**Non-Goals:**

- Changing the teacher panel, authentication flows, or permission model beyond import/export permissions.
- Import/export for any model other than `Student`.
- Real-time updates, scheduled reports, or advanced analytics.
- Custom user model changes (though the project may introduce one later independently).

## Decisions

### 1. Use `django-unfold` as a theme, not a separate admin site

We will add `unfold` to `INSTALLED_APPS` before `django.contrib.admin` and inherit all admin classes from `unfold.admin.ModelAdmin`. This avoids touching `urls.py` or creating a custom `AdminSite`, and keeps the existing `/admin/` URL and login redirects working. If we later need deeper customization, we can switch to `UnfoldAdminSite`.

### 2. Build the Reports page as a custom Unfold admin view

Unfold supports custom pages via `UnfoldModelAdminViewMixin` plus a `ModelAdmin.get_urls()` hook. We will attach the Reports page to `AttendanceSessionAdmin` (a natural home for attendance reporting) and register the URL in `UNFOLD["SIDEBAR"]["navigation"]` so it appears in the sidebar. The view will require `is_staff`.

Alternative considered: overriding `templates/admin/index.html` and using `DASHBOARD_CALLBACK`. We are choosing a separate Reports page because it is easier to link directly, simpler to permission, and keeps the admin index uncluttered. The dashboard callback pattern remains available for a future home-page dashboard.

### 3. Use Unfold chart components for bar/line and Chart.js directly for the pie chart

Unfold ships `unfold/components/chart/bar.html` and `unfold/components/chart/line.html`. It does not ship a pie component, but it already loads Chart.js. We will render the pie chart with a small inline Chart.js canvas in the Reports template, reusing Unfold’s CSS color variables where possible.

### 4. Aggregate data with plain ORM queries

The Reports view will compute:

- Total students, total classrooms, and sessions in the selected date range.
- `AttendanceRecord.objects.values('status').annotate(count=...)` for the pie chart.
- `AttendanceRecord.objects.annotate(day=TruncDate('session__date')).values('day', 'status').annotate(count=...)` for the line chart.
- `AttendanceRecord.objects.values('session__classroom__subject__name', 'status').annotate(count=...)` (or similar) for the bar chart.

For school-sized data on SQLite this is sufficient. If data grows, we can cache the aggregates or materialize them later.

### 5. Use `django-import-export` with Unfold-styled forms

We will add `django-import-export` and an XLSX backend (`openpyxl`). `StudentAdmin` will inherit from both `unfold.admin.ModelAdmin` and `import_export.admin.ImportExportModelAdmin`, using `unfold.contrib.import_export.forms.ImportForm` and `ExportForm`. We will define a `StudentResource` in a new `src/school/resources.py` that maps `first_name`, `last_name`, `email`, and `student_groups` (comma-separated group names via `ManyToManyWidget`).

### 6. Keep resources close to the admin

`StudentResource` will live in `src/school/resources.py` and be referenced from `StudentAdmin`. This keeps import/export logic discoverable and testable without mixing it into `models.py`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Unfold releases are frequent; a future version may change template/component APIs. | Pin a known-compatible version in `pyproject.toml` and verify with `uv run manage.py check` after any upgrade. |
| Importing students with duplicate emails or malformed group names could create bad data. | Use `django-import-export` dry-run/preview by default and declare `skip_unchanged = True`. Add validation in the resource. |
| The pie chart is not a built-in Unfold component, so it may need manual styling updates if Unfold’s CSS variables change. | Use Unfold CSS variables (`--color-primary-*`) and keep the chart snippet small and isolated. |
| Aggregating attendance records in real time may become slow as the database grows. | The current scope is small; if needed later, add caching or a materialized reporting table. |
| Adding `unfold.contrib.import_export` before `django.contrib.admin` requires correct `INSTALLED_APPS` ordering. | Document the order in `design.md` and verify via Django checks. |

## Migration Plan

1. Add dependencies and run `uv lock` / `uv sync`.
2. Update `INSTALLED_APPS` ordering.
3. Refactor `src/school/admin.py` to use Unfold base classes.
4. Add `StudentResource` and wire it into `StudentAdmin`.
5. Create the Reports view, template, and sidebar entry.
6. Run `uv run manage.py check`, perform manual smoke tests, and confirm import/export preview works.

## Open Questions

- Should the Reports page have a date-range filter in its first version, or default to the current school term / last 30 days?
- Should the Student export include the internal `id` column to support round-trip updates, or only human-readable fields?
