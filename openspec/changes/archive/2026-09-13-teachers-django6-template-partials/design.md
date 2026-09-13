## Context

The `teachers` app is a Django + HTMX panel. Today each HTMX-swappable fragment lives in its own file:

| Partial file | Rendered in isolation by |
|---|---|
| `session_detail/session_header_partial.html` | `SessionUpdateView.post` (success) |
| `session_detail/session_form_partial.html` | `SessionUpdateView.get` and `post` (errors) |
| `session_detail/attendance_panel_partial.html` | `SessionDetailView.post` → `_render_panel` |
| `session_detail/attendance_form_partial.html` | (included only) |
| `session_detail/attendance_table_partial.html` | (included only) |
| `session_detail/attendance_readonly_partial.html` | (included only) |
| `session_detail/record_status_button_partial.html` | `RecordToggleStatusView.post` |
| `course_session_history/session_list_partial.html` | (included only) |
| `course_detail/session_panel_partial.html` | (included only) |

Full pages pull fragments in with `{% include %}`. The project runs Django 6.1.1 with `django-htmx` (middleware + `{% htmx_script %}`); `django-template-partials` was never installed, so there is no third-party package to migrate away from — Django 6's built-in template partials are the direct replacement.

Environment constraints: `uv` manages the env (`uv run manage.py ...`); no test suite or linter; minimum verification is `uv run manage.py check` plus manual smoke tests.

## Goals / Non-Goals

**Goals:**

- Use Django 6 template partials as the single mechanism for HTMX fragments: `{% partialdef %}`/`{% partial %}` within host templates, and `render(request, "host.html#partial_name", ctx)` in endpoint views.
- Co-locate each fragment with the page that owns it (Locality of Behaviour) and delete the 9 separate partial files.
- Preserve behavior exactly: same HTML output, same HTMX wire format, same contexts, same retargeting.

**Non-Goals:**

- Any user-visible change, URL change, or spec requirement change (see proposal).
- Touching `base.html`, login/dashboard templates, `course_detail.py`, `course_session_history.py`, `dashboard.py`, `auth.py`, `mixins.py`, forms, models, or settings.
- Resolving the pre-existing divergence between the teacher-panel spec and the actual create-session flow.

## Decisions

**D1: Where each partial lives.** Each fragment moves into the host page template that currently `{% include %}`s it. Mapping:

- `session_detail_template.html` (absorbs 6 files):
  - `session_header` ← session_header_partial.html
  - `session_form` ← session_form_partial.html
  - `attendance_panel` ← attendance_panel_partial.html + attendance_form_partial.html + attendance_table_partial.html (merged: messages `<ul>` + form + table)
  - `attendance_readonly` ← attendance_readonly_partial.html
  - `record_status_button` ← record_status_button_partial.html
- `course_session_history_template.html`: `session_list` ← session_list_partial.html
- `course_detail_template.html`: `session_panel` ← session_panel_partial.html

Alternative considered: keeping separate files and only using `#partial` access — rejected; it would keep the sprawl partials exist to fix.

**D2: Definition style.** Partials are defined without `inline`, then placed with `{% partial name %}` where the `{% include %}` used to be; the conditional `#attendance-panel` content becomes `{% if editable %}{% partial attendance_panel %}{% else %}{% partial attendance_readonly %}{% endif %}`. In `session_detail_template.html` the five definitions sit after `{% endblock %}` (registered at parse time; never rendered by `{% extends %}` — keeps full-page output byte-identical, verified by diff). In the other two hosts, `{% partialdef ... inline %}` definitions sit inside their target div so the inline render occupies the exact include position. Alternative considered: `{% if %}`-wrapped inline definitions at the usage site — rejected after whitespace artifacts showed up in byte-diffs.

**D3: Per-row button context.** `record_status_button` is used per formset row via `{% with record=form.instance %}{% partial record_status_button %}{% endwith %}` — the documented pattern for adjusting partial context (`{% partial %}` takes no arguments).

**D4: View call sites (mechanical).** In `views/session_detail.py` only template names change:

- `_render_panel` → `'teachers/session_detail/session_detail_template.html#attendance_panel'`
- `RecordToggleStatusView.post` (both branches) → `...#record_status_button`
- `SessionUpdateView.get` + `post` error path → `...#session_form`
- `SessionUpdateView.post` success → `...#session_header`

Contexts, `retarget()` calls, messages, and `STATUS_CYCLE` logic are untouched.

**D5: No merge of `session_form` into the panel.** `session_form` is HTMX-fetched only; keeping it a distinct partial preserves the GET endpoint and the error-retarget path as-is.

## Risks / Trade-offs

- [`template.html#partial` on a template with `{% extends %}`] → Documented behavior is that only the fragment renders (extends is not processed); verified in Phase 3 by diffing swap output against pre-refactor captures so HTMX targets stay stable.
- [`{% partial %}` inside a `partialdef` referencing a sibling partial] → Used once (`record_status_button` inside `attendance_panel`'s table). Registration happens at parse time, but the smoke test confirms the rendered table rows; fallback is inlining the button markup into the table loop if isolation fails (would still pass the smoke test, only loses reuse).
- [Context availability in isolated renders] → Partials render with the current context; views already pass the exact context each fragment needs. The smoke test covers each endpoint, including error paths that add `errors`/`formset`.
- [Larger host templates] → `session_detail_template.html` grows (~120 lines). Accepted trade-off: one file per page beats 6 scattered fragments; this is the trade the feature was designed for.
- [No test suite] → Byte-diff of rendered HTML (pre/post captures via curl against runserver) plus exercising every HTMX flow manually; `uv run manage.py check` as the baseline gate.

## Migration Plan

1. Implement template + view changes (tasks.md).
2. Capture pre-refactor HTML for the 4 full pages and each HTMX response; compare post-refactor output.
3. Delete the 9 partial files only after output matches.
4. Rollback: single revert of the change (no data/migrations involved).

## Open Questions

None.
