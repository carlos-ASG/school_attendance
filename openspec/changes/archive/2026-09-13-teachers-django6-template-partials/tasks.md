## 1. Capture pre-refactor baseline

- [x] 1.1 Start the dev server (`uv run manage.py runserver`), log in as a teacher, and capture rendered HTML of the 4 full pages (dashboard, course detail, session history, session detail — editable and read-only variants) plus each HTMX response (status toggle, attendance save success/error, session edit GET/success/error) to a temp directory for later byte-diffing
- [x] 1.2 Run `uv run manage.py check` and confirm a clean baseline

## 2. Convert session detail templates

- [x] 2.1 In `teachers/templates/teachers/session_detail/session_detail_template.html`, define partials at the top of `{% block content %}`: `session_header`, `session_form`, `attendance_panel` (absorbing attendance_panel_partial + attendance_form_partial + attendance_table_partial: messages `<ul>`, form, table), `attendance_readonly`, and `record_status_button` — copying each file's markup verbatim
- [x] 2.2 Replace the `{% include %}` calls in the same template with `{% partial %}` usage: `{% partial session_header %}` in `#session-header`; `{% if editable %}{% partial attendance_panel %}{% else %}{% partial attendance_readonly %}{% endif %}` in `#attendance-panel`
- [x] 2.3 Render `record_status_button` per formset row via `{% with record=form.instance %}{% partial record_status_button %}{% endwith %}` inside the `attendance_panel` table loop

## 3. Convert remaining host templates

- [x] 3.1 In `teachers/templates/teachers/course_session_history/course_session_history_template.html`, define `session_list` as `{% partialdef session_list inline %}` and replace the `{% include %}` in `#session-list` (markup copied verbatim from session_list_partial.html)
- [x] 3.2 In `teachers/templates/teachers/course_detail/course_detail_template.html`, define `session_panel` as `{% partialdef session_panel inline %}` and replace the `{% include %}` in `#session-panel` (markup copied verbatim from session_panel_partial.html)

## 4. Update views to `#partial` rendering

- [x] 4.1 In `src/teachers/views/session_detail.py`, point `_render_panel` at `teachers/session_detail/session_detail_template.html#attendance_panel` (both call paths: success and invalid-formset with `retarget`)
- [x] 4.2 Point `RecordToggleStatusView.post` success and validation-error branches at `...session_detail_template.html#record_status_button` (error branch keeps `errors` in context)
- [x] 4.3 Point `SessionUpdateView.get` and its `post` error branch at `...#session_form` (keep `retarget(response, '#session-edit')`), and the `post` success branch at `...#session_header`
- [x] 4.4 Confirm no other view file references the deleted partial names (`grep` the views package)

## 5. Delete superseded files

- [x] 5.1 Delete the 9 partial files: `session_header_partial.html`, `session_form_partial.html`, `attendance_panel_partial.html`, `attendance_form_partial.html`, `attendance_table_partial.html`, `attendance_readonly_partial.html`, `record_status_button_partial.html`, `session_list_partial.html`, `session_panel_partial.html`
- [x] 5.2 Grep the repo to confirm no remaining references to any deleted template name

## 6. Verify behavior is identical

- [x] 6.1 Run `uv run manage.py check` (passes) and `uv run manage.py runserver` for manual testing
- [x] 6.2 Byte-diff the 4 full pages' HTML against the 1.1 baseline (only acceptable diff: none)
- [x] 6.3 Exercise every HTMX flow and diff each response against baseline: cycle a status button (success), force a validation error path on toggle, save attendance (success), submit invalid attendance (retargeted panel with errors), fetch edit-date form, submit valid date change (header swap), submit invalid date (form + retarget), delete session (HX-Redirect to history page)
- [x] 6.4 Verify `render("...session_detail_template.html#partial")` on the `{% extends %}`-based template returns only the fragment with no base.html chrome (implicit in 6.3 diffs)

## 7. Wrap up

- [x] 7.1 Run `openspec validate teachers-django6-template-partials --type change` and confirm the delta spec scenarios (fragment responses) are satisfied by the implementation
- [x] 7.2 Mark all tasks complete and request archive of the change (`openspec archive --skip-specs` per design: no requirement deltas)
