# Design: split-session-detail-pages

## Context

The teacher panel currently renders one session page (`teachers/session_detail.html` + `SessionDetailView`) for two distinct workflows: taking today's attendance (always editable, cyclic status buttons, per-action HTMX saves) and reviewing/correcting past sessions (read-only + `?edit=1`, date changing, deletion). The `editable`/`edit_mode` conditionals leak into every fragment endpoint, and session entry points are scattered across the course detail page. The repo's `django6-htmx` skill governs fragment architecture: `{% partialdef %}` blocks live in their host page template, `{% partial %}` only reaches partials in the same file, and fragment endpoint views live in the same module as their page view. The `shadcn-django` skill governs UI components (cotton components, Alpine-powered, owned source in `src/core_ui/templates/cotton/`).

Key constraint that shaped this design: because `{% partial %}` is same-template-only, splitting the session page would normally force duplicating shared fragments (`attendance_panel`, `record_status_button`). The decision to give the previous page its own batch edit form (combobox per row) eliminates all shared fragments — every fragment ends up with exactly one home.

## Goals / Non-Goals

**Goals:**

- One page per workflow: today (live attendance) vs. previous (review/correct), each with its own template, fragments, URL, and view module.
- Consolidate session management on the history page (create past session, view, delete) and today-session access on the dashboard + course detail cards.
- Batch edit form for past sessions: status combobox + notes per row, saved only on submit, then drop to read-only.
- Remove session date editing entirely.

**Non-Goals:**

- Model/schema/migration changes; admin changes; auth changes (see proposal Non-goals).
- State-aware dashboard button labels ("Ir" vs "Crear") — single get-or-create button; annotation polish later.

## Decisions

### D1: Two named URLs with redirect guards (not one URL with dynamic template)

```
courses/<pk>/sessions/today/   POST  today_session_create   get-or-create → redirect to detail
sessions/<pk>/today/           GET   today_session_detail   guard: date != today → redirect to session_detail
sessions/<pk>/                 GET   session_detail         guard: date == today → redirect to today_session_detail
```

Rationale: URL-level enforcement of the access split; self-documenting intent; deep links and bookmarks resolve to the correct page. A single URL with `get_template_names()` was considered (less code) but leaves the split implicit and gives fragment endpoints a date-branching helper anyway — no net win. Guards are plain redirects (302), not 404s, so stale links keep working. A tiny `session_detail_url(session)` helper centralizes the date→URL routing.

### D2: Fragment ownership — no shared fragments, no template inheritance

```
today_session_detail.html        previous_session_detail.html      course_session_history.html
├─ #session_header (back→curso)  ├─ #session_header (back→historial, "Editar" link → ?edit=1)
├─ #attendance_panel             ├─ #attendance_readonly           ├─ #session_create_form (NEW)
│   (toggle + notas + delete      ├─ #attendance_edit_form (NEW)   └─ #session_list (+ Acciones column)
│    alert-dialog)               └─ (no session_form — removed)
└─ #record_status_button
```

`RecordToggleStatusView` serves only the today page and renders `today_session_detail.html#record_status_button` unconditionally. Template inheritance for partial sharing was considered and dropped: unnecessary once the previous page stops using the toggle panel, and unverified in this stack.

### D3: View module layout (page view + its fragment endpoints together)

- `views/today_session.py` (new): `TodaySessionCreateView` (POST-only get-or-create), `TodaySessionDetailView` (GET + POST notes-formset save), `RecordToggleStatusView` (moved here).
- `views/session_detail.py` → previous page: `PreviousSessionDetailView` (GET read-only / `?edit=1`; POST edit-formset batch save). `SessionUpdateView` and `STATUS_CYCLE`-adjacent date logic deleted (STATUS_CYCLE stays with the toggle view).
- `views/course_session_history.py`: `CourseSessionHistoryView` gains `post()` (create past session — repo precedent: page views handle their own POSTs, as `CourseDetailView` does today), plus `SessionDeleteView` (moved here because its primary response re-renders `#session_list`).
- `views/course_detail.py`: `post()`, `dispatch()` form stashing, `_create_today_session()` all deleted — pure `DetailView` again.
- `views/dashboard.py`: unchanged (no annotation for now).

### D4: Today-session get-or-create endpoint

`POST courses/<pk>/sessions/today/` reuses the existing get-or-create semantics from `CourseDetailView._create_today_session()` (create with records if missing, else reuse). Both the dashboard card and the course detail card POST here via a plain `<form method="post">` (no `hx-post`) — a full-page redirect is the desired outcome and it works without JS, matching the current course-detail pattern.

### D5: Status control per page — toggle vs. combobox

- Today page keeps the cyclic `record_status_button` (instant per-record HTMX saves) + notes formset (`AttendanceFormSet`, notes-only, unchanged).
- Previous-page edit mode gets a NEW `AttendanceEditFormSet` (`modelformset_factory(AttendanceRecord, fields=('status', 'notes'))`): one row per student, status chosen from a combobox, nothing persisted until submit; `formset.save()` persists all changes, then the view renders `#attendance_readonly` into `#attendance-panel` (drop to read-only, per product decision).
- Combobox strategy (in order): (1) `uvx shadcn_django@latest add combobox` (or `select`), move source into `src/core_ui/templates/cotton/`, wire a hidden `<input name="form-<i>-status">` synced to the Alpine state — owning/editing copied component source is the sanctioned pattern; (2) if formset serialization (management form, `form-N-` prefixes) fights the component, fall back to a native `<select>` styled with shadcn trigger classes — free form POST semantics, keyboard a11y, no-JS safe.

### D6: History page — create form + actions column

- Top card "Crear sesión en otra fecha": `SessionForm` posted to the history URL; HTMX errors re-render `#session_create_form` + `retarget` (repo error pattern), non-HTMX errors re-render the full page with the bound form.
- `SessionForm` validation becomes strictly past-only: reject `date >= today` (future: existing message; today: "Para la sesión de hoy, usa la tarjeta 'Sesión de hoy'"). The `exclude_pk` parameter is deleted along with the update flow.
- Table columns: Date (plain text) | Created | Acciones ([Ver] button → previous detail; [Eliminar] behind `c-alert-dialog`). Navigation is single-path through Acciones (removes the current date-as-link).
- Delete via HTMX re-renders `course_session_history.html#session_list` with the fresh queryset (target `#session-list`, `innerHTML` swap) instead of the current `HX-Redirect` — the redirect only existed because deletes came from a page that ceased to exist; from the history page the list just updates, and the empty state renders naturally. Non-HTMX fallback: redirect to the history page.
- `SessionDeleteView` branches on `session.date == today`: today-session deletes (from the today page's alert dialog) redirect to the course detail page (the card returns to its "create" state); past-session deletes re-render the history list.
- Queryset excludes today's session (`exclude(date=today)`); a today session automatically appears in history after midnight (runtime date comparison — no data job needed).

### D7: Dashboard & course detail cards

- Per course: existing info card, then a `grid grid-cols-2` row with two compact shadcn cards (header + footer only, no content): "Sesión de hoy" (single button, e.g. "Tomar asistencia", POST → D4 endpoint) and "Historial de sesiones" (footer link/button → history page).
- Course detail: the `session_panel` partialdef block is deleted; replaced by the same "Sesión de hoy" compact card; the bottom "Ver sesiones" link is kept (re-styled as a button). All copy in Spanish per repo rule.

## Risks / Trade-offs

- [Combobox × formset: N Alpine instances + hidden inputs + `form-N-status` prefixes] → Probe early in implementation with the byte-diff-style test-client script; the native-select fallback is fully specified so switching costs one task, not a redesign.
- [Removing date editing makes "wrong date" recovery destructive: delete + recreate regenerates records as PRESENT and loses notes] → Accepted product decision; the delete confirmation dialog explicitly warns that records are removed.
- [Old bookmarks to `sessions/<pk>/` for a today session now redirect to `/today/`] → Intended behavior (guards), one extra hop, no breakage.
- [Three cards per course may feel heavy with many courses] → Compact cards, grid row; can collapse into the course card footer later if it reads poorly.
- [Per-row alert dialogs in the table add Alpine weight] → Same pattern already proven in the session panel; acceptable.
- [Fragment endpoints and templates renamed/removed — stale references] → Grep for `session_detail.html#`, `session_edit`, `session_panel`, `session_form` during implementation; `uv run manage.py check` + smoke script as verification (this is a behavior-changing refactor, so the byte-diff no-diff harness does not apply; instead verify each new flow renders and round-trips via the Django test client).

## Migration Plan

Single deploy: URL surface changes are internal to the teacher panel (no external consumers, no API). No data migration. Rollback = revert commit; templates/views are self-contained.

## Open Questions

- ~~Combobox vs. native select final call~~ — **Resolved during implementation (D5 probe):** the copied `select` cotton component renders standalone, but its Alpine state hardcodes `value: ''` (no initial/default value support — rows would open showing the placeholder instead of the record's current status), the hidden input is only populated via `x-bind:value` (empty submit without JS), and the div-listbox has no keyboard navigation. Chose the pre-approved fallback: native `<select>` styled with shadcn trigger classes via widget attrs (form POST semantics, initial value, keyboard a11y, no-JS safe). The unused copied component was removed after the probe.
