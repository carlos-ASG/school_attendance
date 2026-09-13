## Why

The course detail page mixes course information (schedule, roster, attendance summary) with full session management (create, edit, delete), making it long and cluttered. Separating the session list into its own page keeps the course page focused. In addition, opening a past session currently offers an editable attendance form by default, which risks accidental edits of historical attendance; past sessions should be read-only until the teacher explicitly enables editing.

## What Changes

- Add a dedicated course sessions page (`courses/<int:pk>/sessions/`) backed by a class-based `ListView`, showing the course's sessions and the create-session form (HTMX), with a link back to the course.
- Slim down `course_detail.html` to course info, schedule, student attendance summary, the existing "Crear sesión de hoy" / "Sesión de hoy" shortcut, and a button linking to the new sessions page.
- Remove the session panel (create form + sessions table) from `course_detail.html`.
- Remove edit/delete buttons from the session list; move session editing (date) and deletion entirely to the session detail page.
- Require an explicit confirmation message before deleting a session from the session detail page.
- On the session detail page, make attendance editable by default only for today's session; past sessions render read-only with an "Editar" button that enables editing.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `teacher-panel`: Course detail no longer embeds the session list; a new course sessions page (class-based `ListView`) hosts the session list and creation form; session edit/delete controls move entirely to the session detail page, with delete requiring a confirmation; session detail attendance is editable by default only for today's session — past sessions are read-only until the teacher clicks an edit control.

## Impact

- `src/teachers/views.py`: new `CourseSessionListView` (ListView with a POST handler for session creation); `CourseDetailView` loses the session-panel context and date-based creation POST (keeps "create today"); `SessionDetailView` gains read-only vs. editable attendance modes and hosts session edit/delete UI.
- `src/teachers/urls.py`: new route `courses/<int:pk>/sessions/` named `course_sessions`.
- Templates: new `teachers/course_session_list.html`; updates to `course_detail.html`, `session_detail.html`, and partials `session_panel.html`, `session_list.html`, `session_form.html`, `attendance_panel.html`/`attendance_table.html`.
- HTMX flows: create/edit/delete targets change accordingly; delete uses a confirm message (`hx-confirm`).
- No model, migration, or dependency changes.

## Non-goals

- No pagination of the sessions list.
- No changes to attendance models, statuses, or the admin site.
- No audit log or change history for past-session edits.
- No changes to the attendance summary calculation on the course page.
