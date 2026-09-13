## Context

The teacher panel lives in `src/teachers/` (Django CBVs + HTMX). Today `CourseDetailView` serves course info, the student attendance summary, and the whole session panel (create-today shortcut, date-based create form, session list with HTMX edit/delete) — the panel partials `session_panel.html` / `session_list.html` are swapped in place via HTMX targets `#session-list`. `SessionDetailView` renders `session_detail.html` with the editable attendance formset regardless of the session date. `SessionUpdateView` and `SessionDeleteView` return row/list partials consumed from the course page.

Constraints: no test suite or linter (`uv run manage.py check` is the verification floor); all panel text in Spanish; HTMX-driven UX; the active `course-detail-attendance-percentage` change touches the same course detail files.

## Goals / Non-Goals

**Goals:**
- Move the session list and the date-based create form to a dedicated page `courses/<int:pk>/sessions/` served by a class-based `ListView`.
- Reduce `course_detail.html` to course info, schedule, student attendance summary, today-session shortcut, and a button to the sessions page.
- Move session edit/delete controls entirely to the session detail page; deletion requires a confirmation message.
- Attendance on `session_detail` is editable by default only for today's session; past sessions render read-only until the teacher clicks an edit control.

**Non-Goals:**
- Pagination, audit logging, model/migration changes, changes to the admin site or attendance summary logic.

## Decisions

1. **New `CourseSessionListView(TeacherRequiredMixin, ListView)` owning creation.**
   The view resolves the course with `get_object_or_404(Course.objects.filter(teacher=self.teacher), pk=kwargs['pk'])` (denies other teachers' courses), lists `course.sessions` via `get_queryset`, and handles `POST` with `SessionForm` for date-based creation (the logic currently in `CourseDetailView.post`). HTMX submissions re-render `session_list.html` into `#session-list`; non-HTMX submissions re-render the full page so validation errors are visible.
   *Alternatives:* keep creation on `CourseDetailView` and make the new page read-only (rejected: session management should live together); function-based view (rejected: user explicitly wants a generic `ListView`, and the project is CBV-based).

2. **Today-session creation stays on `CourseDetailView`.**
   `CourseDetailView` keeps only the `create_today` POST branch and the `today_session` context (needed by the "Sesión de hoy"/"Crear sesión de hoy" shortcut); it drops `sessions`, `form`, and the date-form POST.
   *Alternative:* move the shortcut to the sessions page (rejected by user).

3. **Session edit/delete move to `session_detail.html` and become non-row HTMX.**
   `session_detail.html` gains a controls area with a `#session-edit` container: an "Editar sesión" button loads `session_form.html` via `hx-get` into it; submission POSTs to `session_edit`, which on success re-renders the session header in place (HTMX) or redirects (non-HTMX). "Eliminar sesión" uses `hx-post` + `hx-confirm` targeting the controls area; on success the view responds with `HX-Redirect` to `course_sessions` (plain redirect for non-HTMX), since the list no longer exists on that page to re-render.
   *Alternatives:* keep edit/delete in the list (rejected by user); full-page form for edit (rejected: project UX is HTMX-in-place).

4. **Read-only attendance via an `editable` flag computed in `get_context_data`.**
   `editable = (session.date == timezone.now().date()) or (self.request.GET.get('edit') == '1')`. When editable, the page renders the existing `attendance_panel.html` (formset). When not, it renders a new read-only partial (`attendance_readonly.html`: student, `get_status_display`, notes) inside the same `#attendance-panel` target. The edit toggle is a plain link `?edit=1` — no extra JS, works without HTMX, and the URL is shareable/bookmarkable.
   *Alternatives:* HTMX-driven toggle (more moving parts for no gain); separate read-only view URL (duplicates auth/queryset logic).

5. **Button wording to avoid two identical "Editar" labels.**
   The attendance edit toggle keeps the label "Editar" (per user request); the session's own controls are labeled "Editar sesión" and "Eliminar sesión" to disambiguate.

6. **Keep DOM ids stable (`#session-list`, `#attendance-panel`) so existing HTMX swap targets keep working after the move.**

## Risks / Trade-offs

- [Spec delta conflict: `course-detail-attendance-percentage` also MODIFIES "Course detail view"] → our delta carries its attendance-summary scenarios forward; archive this change after that one (or merge manually) so no scenario is lost.
- [Edit/delete partials were row-scoped (`hx-target="closest tr"`)] → rework targets to page-level containers; verify each HTMX flow manually after implementation.
- [Delete from detail page cannot re-render a list in place] → use `HX-Redirect` to the sessions page; non-HTMX fallback redirects normally.
- [Crafted POST could toggle/save records of past sessions without the UI toggle] → acceptable: the spec explicitly allows enabling editing for past sessions; no server-side restriction added.

## Migration Plan

No data or dependency changes; deployment is a code deploy. Rollback is a revert. The only spec-level touchpoint is archiving this delta after (or merged with) `course-detail-attendance-percentage`.

## Open Questions

None — scope and behavior were confirmed with the user (Option B, edit/delete on session detail, shortcut stays on course detail, URL `courses/<int:pk>/sessions/`).
