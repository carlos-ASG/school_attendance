## 1. Dependency and app setup

- [x] 1.1 Add `django-htmx` to `pyproject.toml` dependencies and run `uv sync`
- [x] 1.2 Add `django_htmx` to `INSTALLED_APPS` and `django_htmx.middleware.HtmxMiddleware` to `MIDDLEWARE`
- [x] 1.3 Create the new Django app `teachers` in `src/teachers/` (`uv run manage.py startapp teachers src/teachers`)
- [x] 1.4 Add `teachers` to `INSTALLED_APPS` and to `pyproject.toml` `module-name` list
- [x] 1.5 Verify `uv run manage.py check` passes with the new app wired in

## 2. Domain model and migration changes

- [x] 2.1 Rename `Classroom` model to `Course` in `src/school/models.py`, update `Meta` options, verbose names, and constraint name
- [x] 2.2 Rename FK fields `classroom` → `course` on `AttendanceSession` and `ClassSchedule`, and update related names (`classrooms` → `courses`)
- [x] 2.3 Add `Course.classroom = CharField('Aula', max_length=50, blank=True, default='')`
- [x] 2.4 Remove `notes` from `AttendanceSession`
- [x] 2.5 Add `AttendanceRecord.notes = TextField('Notas', blank=True, default='')`
- [x] 2.6 Add `updated_at = DateTimeField('Última actualización', auto_now=True, null=True, blank=True)` to `Course`, `AttendanceSession`, and `AttendanceRecord`
- [x] 2.7 Generate migrations with `uv run manage.py makemigrations`, review them, and run `uv run manage.py migrate`

## 3. Admin and validation

- [x] 3.1 Update `src/school/admin.py` imports and registrations from `Classroom` to `Course`
- [x] 3.2 Update `ClassScheduleInline` and `AttendanceRecordInline` for the renamed `Course` model
- [x] 3.3 Scope the `AttendanceRecordInline.student` dropdown to members of `session.course.student_group`
- [x] 3.4 Add `AttendanceRecord.clean()` to raise `ValidationError` when `student` is not in `session.course.student_group`
- [x] 3.5 Create a data migration that adds a `Administradores de solo lectura` group with view-only permissions on all `school` models
- [x] 3.6 Verify the admin site loads, lists courses, and rejects out-of-group students in the attendance inline

## 4. Extract teacher panel to `teachers` app

- [x] 4.1 Move teacher-facing views from `src/school/views.py` to `src/teachers/views.py`, updating all `Classroom`/`classroom` references to `Course`/`course`
- [x] 4.2 Move teacher-facing forms from `src/school/forms.py` to `src/teachers/forms.py`
- [x] 4.3 Move teacher URLs from `src/school/urls.py` to `src/teachers/urls.py` with `app_name = 'teachers'` and paths under `/teacher/`
- [x] 4.4 Move panel templates from `src/school/templates/school/` to `src/teachers/templates/teachers/`
- [x] 4.5 Update `src/config/urls.py` to include `teachers.urls` under `teacher/` and remove panel paths from `school.urls`
- [x] 4.6 Clean up leftover panel code from `src/school/views.py`, `src/school/forms.py`, and `src/school/urls.py`
- [x] 4.7 Verify the panel dashboard, course detail, and session detail pages render for a logged-in teacher

## 5. Session CRUD and htmx reactivity

- [x] 5.1 Add `SessionUpdateView` in `teachers/views.py` to edit an attendance session's date with htmx-aware partial rendering
- [x] 5.2 Add `SessionDeleteView` in `teachers/views.py` to delete a session with `hx-confirm` and htmx partial rendering
- [x] 5.3 Update `CourseDetailView` to render a session list partial and swap it after create/edit/delete via htmx
- [x] 5.4 Update `SessionDetailView` to return the attendance partial on htmx POSTs and use `retarget()` for form errors
- [x] 5.5 Update the panel base template to load `{% htmx_script %}` and set `hx-headers='{"x-csrftoken": "{{ csrf_token }}"}'`
- [x] 5.6 Add/update partial templates: `session_list.html`, `session_form.html`, `attendance_table.html`, and `attendance_form.html`
- [x] 5.7 Replace the attendance status radio buttons with a cycling status button that persists immediately via htmx, rotating Presente → Ausente → Tarde → Justificado → Presente
- [x] 5.8 Add a dedicated `RecordToggleStatusView` and `record_status_button.html` partial for per-record status updates
- [x] 5.9 Include the `notes` field in the attendance panel formset and allow teachers to save notes per student
- [x] 5.10 Verify create, edit, and delete operations update the relevant page fragment without a full reload
- [x] 5.11 Verify status cycling and note saving work end-to-end in the teacher panel

## 6. Tests and final verification

- [x] 6.1 Add a test that `AttendanceRecord.clean()` raises `ValidationError` when the student is not in the course group
- [x] 6.2 Add a test that the admin `AttendanceRecordInline` limits the `student` choices to the course group
- [x] 6.3 Add tests for teacher panel session create, update, and delete views
- [x] 6.4 Run `uv run manage.py check`, `uv run manage.py migrate`, and the test suite
- [x] 6.5 Smoke-test the admin and teacher panel end-to-end
