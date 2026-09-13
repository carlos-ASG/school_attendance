## Why

The `teachers` app follows the pre-Django 6 HTMX pattern: 9 separate `*_partial.html` fragment files, `{% include %}` from full pages, and 6 `render(..., partial_file)` call sites in views. Django 6 introduced built-in template partials (`{% partialdef %}` / `{% partial %}` and the `template.html#partial_name` render syntax), designed exactly for this HTMX fragment flow. Migrating keeps the app idiomatic to the Django version in use (6.1) and removes template file sprawl, co-locating each fragment with the page that owns it.

## What Changes

- Replace the 9 separate partial template files with `{% partialdef %}` fragments defined inside their host page templates:
  - `session_detail_template.html` gains `session_header`, `session_form`, `attendance_panel`, `attendance_readonly`, `record_status_button` (absorbing 6 partial files)
  - `course_session_history_template.html` gains `session_list`
  - `course_detail_template.html` gains `session_panel`
- Switch the 6 HTMX endpoint `render()` calls in `src/teachers/views/session_detail.py` to the `template_name#partial_name` syntax; contexts, retargeting, and messages logic unchanged.
- Delete the 9 `*_partial.html` files (15 templates → 6).
- No behavior change: rendered HTML, URLs, HTMX wire format, and view logic are byte-identical.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `teacher-panel`: Adds one requirement codifying the HTMX fragment-rendering contract (each swap endpoint returns only its template partial, defined via Django 6 `{% partialdef %}` in host page templates). No existing requirement changes — all prior behavior is preserved byte-for-byte; this documents the wire contract the refactor must keep.

## Impact

- Templates: `src/teachers/templates/teachers/session_detail/*`, `course_session_history/*`, `course_detail/*` (3 host templates modified, 9 files deleted).
- Views: `src/teachers/views/session_detail.py` (template-name strings only).
- No changes to: `urls.py`, forms, models, settings, `base.html`, login/dashboard templates, dependencies, or migrations.
- Verification: `uv run manage.py check` plus manual smoke tests of every HTMX flow.

## Non-goals

- Changing any user-visible behavior, HTML structure, or HTMX interaction.
- Aligning the pre-existing spec/implementation divergence around the create-session form (course detail page with plain POST vs. the spec's HTMX on the sessions page) — a separate change.
- Adopting other Django 6 features (tasks framework, CSP, email API, GeneratedField — not applicable to this codebase).
