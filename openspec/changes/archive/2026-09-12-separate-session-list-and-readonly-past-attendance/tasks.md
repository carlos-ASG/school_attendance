## 1. Course sessions page (backend)

- [x] 1.1 Add `CourseSessionListView(TeacherRequiredMixin, ListView)` to `src/teachers/views.py`: resolve the teacher's course via `get_object_or_404(Course.objects.filter(teacher=self.teacher), pk=kwargs['pk'])`, list `course.sessions` (most recent first) in `get_queryset`, and expose the course in context
- [x] 1.2 Add a `POST` handler to `CourseSessionListView` that creates a session from `SessionForm` (date-based), generates records via `create_attendance_records`, and on HTMX requests re-renders `teachers/partials/session_list.html` into `#session-list`, on non-HTMX requests re-renders the full page with validation errors
- [x] 1.3 Add route `courses/<int:pk>/sessions/` named `course_sessions` to `src/teachers/urls.py`
- [x] 1.4 Create template `src/teachers/templates/teachers/course_session_list.html` extending `teachers/base.html`: course heading, back link to course detail, include of `teachers/partials/session_panel.html`

## 2. Session creation moves off the course page (backend)

- [x] 2.1 Slim `CourseDetailView` in `src/teachers/views.py`: drop the `sessions` and `form` context entries and the date-form branch of `post`, keep the `create_today` branch and the `today_session` context
- [x] 2.2 Update `teachers/partials/session_panel.html`: point the create form's `action` and `hx-post` at `teachers:course_sessions`

## 3. Session list loses row controls (templates)

- [x] 3.1 Update `teachers/partials/session_list.html`: remove the Editar/Eliminar buttons and the Actions column; each row keeps the date link to `session_detail`

## 4. Session detail: read-only by default, edit toggle (backend)

- [x] 4.1 In `SessionDetailView.get_context_data` compute `editable = (session.date == timezone.now().date()) or (self.request.GET.get('edit') == '1')` and expose it in context
- [x] 4.2 Create partial `src/teachers/templates/teachers/partials/attendance_readonly.html` listing each record's student, status display, and notes without input controls

## 5. Session detail: controls, read-only UI, edit/delete (templates)

- [x] 5.1 Update `teachers/session_detail.html`: render `attendance_readonly.html` when not editable, `attendance_panel.html` when editable, plus an "Editar" link (`?edit=1`) shown only for past sessions
- [x] 5.2 Add a session controls area with a `#session-edit` container: "Editar sesión" button (`hx-get` to `teachers:session_edit` targeting `#session-edit`) and "Eliminar sesión" button (`hx-post` to `teachers:session_delete`, `hx-confirm` message in Spanish, targeting the controls area)
- [x] 5.3 Rework `SessionUpdateView` responses: on success re-render the session header area in place for HTMX requests (full page redirect otherwise) instead of the `#session-list` row partials
- [x] 5.4 Rework `SessionDeleteView` to respond with `HX-Redirect` to `teachers:course_sessions` for HTMX requests (plain redirect otherwise) instead of re-rendering `session_list.html`

## 6. Course detail slims down (templates)

- [x] 6.1 Update `src/teachers/templates/teachers/course_detail.html`: remove the `<div id="session-panel">` include, keep schedule + students table with attendance summary + today-session shortcut, and add a "Ver sesiones" button linking to `teachers:course_sessions`

## 7. Verification

- [x] 7.1 Run `uv run manage.py check` with no errors
- [x] 7.2 Manually verify flows: course page shows shortcut + "Ver sesiones" button and no session list; sessions page lists sessions with create form (HTMX create updates `#session-list`, duplicate date shows error); session rows have no edit/delete buttons; today's session opens editable, past session opens read-only with "Editar" enabling the formset; HTMX save still updates `#attendance-panel`; "Editar sesión" edits the date in place; "Eliminar sesión" asks for confirmation and redirects to the sessions page
