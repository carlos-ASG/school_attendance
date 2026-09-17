# Proposal: split-session-detail-pages

## Why

A single `session_detail` template and view currently serve two different jobs — taking attendance *now* (today's session) and reviewing/correcting *past* sessions (history) — via `editable`/`edit_mode` conditionals that leak into every fragment endpoint. Session entry points are scattered: today-session creation and the "otra fecha" form both live on the course detail page, while the history page is a read-only list with no management actions. Splitting the pages by session date gives each workflow its own template, fragments, and URL — and lets each page own its UI completely.

## What Changes

- **Split session detail into two pages**: `today_session_detail` (always editable: cyclic status buttons + notes, saved per-action) and `previous_session_detail` (read-only by default with an "Editar" control, reached only from the history page). Each page hosts its own `{% partialdef %}` fragments; no fragments are shared.
- **BREAKING**: session URLs are split — `sessions/<pk>/today/` for today's session, `sessions/<pk>/` for past sessions — with redirect guards so deep links resolve to the correct page.
- **BREAKING**: session date editing is removed everywhere (`SessionUpdateView`, `session_edit` URL, "Cambiar fecha" control, `session_form` fragment). A session created on the wrong date is deleted and recreated.
- **Dashboard**: under each course card, a row of two compact shadcn cards — "Sesión de hoy" (a single create-or-go button that get-or-creates today's session) and "Historial de sesiones" (link to the history page).
- **Course detail**: the session panel is replaced by a "Sesión de hoy" card; the "otra fecha" form moves away; the view loses its POST handlers and becomes a pure read-only `DetailView`.
- **History page**: gains a top "Crear sesión en otra fecha" card (form rejects dates >= today: past only — today is managed from the "Sesión de hoy" card), and the table gains an "Acciones" column with a "ver" button and a "eliminar" button behind a shadcn alert dialog. Deleting re-renders the session list partial in place. Today's session is excluded from the history list.
- **Previous-page edit mode**: a new batch edit form — same fields (student, status, notes) but status is a combobox per row (shadcn combobox with hidden input; fallback: shadcn-styled native `<select>`). Nothing is saved until the form is submitted; on save all changes persist and the page drops back to read-only.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `teacher-panel`: course detail view loses session-creation controls; dashboard gains per-course "Sesión de hoy" and "Historial" cards; the course sessions page gains the create form and per-row actions; session detail splits into today/previous pages with separate URLs and edit semantics; the cyclic status button becomes today-page-only; past-session editing uses a combobox form with batch save; session date editing requirement is removed.

## Impact

- `src/teachers/`: views package restructured (today-session and previous-session page modules with their fragment endpoints; `course_detail.py` POST handling removed; `course_session_history.py` gains create + delete fragments), `forms.py` gains a status+notes edit formset and past-only date validation, `urls.py` re-wired.
- `src/teachers/templates/teachers/`: `session_detail.html` deleted; `today_session_detail.html` and `previous_session_detail.html` added; `dashboard.html`, `course_detail.html`, `course_session_history.html` restructured with shadcn cards.
- `src/core_ui/`: possibly a new combobox/select cotton component (`uvx shadcn_django@latest add`).
- No model changes, no migrations, no admin changes.

## Non-goals

- No `AttendanceSession`/`AttendanceRecord` model or migration changes.
- No changes to domain validation rules in `attendance-tracking` (model-level future-date rejection and today-allowed stay as-is; the past-only rule is form-level on the history create form).
- No Django admin / unfold changes.
- No authentication, login, or role-routing changes.
- No archiving of the completed `add-shadcn-ui` change.
- No state-aware dashboard button labels (single get-or-create button; annotation-based "Ir"/"Crear" labels are future polish).
