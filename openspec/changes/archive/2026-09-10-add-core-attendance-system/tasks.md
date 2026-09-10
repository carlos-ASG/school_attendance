## 1. App scaffold and models

- [x] 1.1 Create the `school` app (`uv run manage.py startapp school`), add it to `INSTALLED_APPS`. Given a fresh checkout, when `uv run manage.py check` runs, then it passes with the app installed.
- [x] 1.2 Implement `Student` (first/last name, optional email, `__str__`), `Teacher` (first/last name, nullable unique OneToOne to `User`), `Subject` (unique name, optional code), `StudentGroup` (name, M2M students) in `school/models.py`. Given the models exist, when migrations are generated, then the tables and unique constraints are created.
- [x] 1.3 Implement `ClassSchedule` (FK classroom, weekday, start_time, end_time) and `Classroom` (FK group, FK teacher, FK subject, `unique_together (teacher, subject, student_group)`). Given an admin, when saving a classroom with a duplicate teacher/subject/group combination, then the save is rejected.
- [x] 1.4 Implement `AttendanceSession` (FK classroom, date, FK created_by teacher, created_at, notes, `unique_together (classroom, date)`) and `AttendanceRecord` (FK session, FK student, status choices PRESENT/ABSENT/LATE/EXCUSED defaulting to PRESENT, `unique_together (session, student)`). Given a session, when it is saved, then one record per group student is auto-generated (shared creation helper used by admin and panel).
- [x] 1.5 Run `uv run manage.py makemigrations school` and `uv run manage.py migrate`. Given an empty database, when migrations run, then all new tables exist.

## 2. Django admin

- [x] 2.1 Register `Student`, `Teacher`, `Subject`, `StudentGroup` ModelAdmins with `list_display`, search and filters (`filter_horizontal` for group students). Given an admin, when browsing these models, then records are searchable and filterable.
- [x] 2.2 Register `Classroom` admin with a `ClassSchedule` tabular inline and a `student_count` list display. Given an admin, when editing a classroom, then schedule slots are editable inline.
- [x] 2.3 Register `AttendanceSession` admin with an `AttendanceRecord` inline and record generation on session creation via the shared helper. Given an admin, when creating a session, then records for all group students appear in the inline.

## 3. Teacher panel foundation

- [x] 3.1 Vendor `htmx.min.js` (pinned version) into `school/static/school/js/`, add `base.html` with nav, messages block, and a small static CSS file. Given any panel page, when rendered, then it extends `base.html` and loads the local htmx script (no CDN).
- [x] 3.2 Add panel auth: `LoginView`/`LogoutView` at `/panel/login/`, `/panel/logout/`, a `TeacherRequiredMixin` (user authenticated AND linked to a Teacher, else deny/redirect), post-login role routing (staff → `/admin/`, teacher → `/panel/`), and a root `/` redirect view. Given an anonymous user, when opening any panel URL, then they are redirected to the login page.

## 4. Teacher panel views and templates

- [x] 4.1 Dashboard view/template listing only `Classroom.objects.filter(teacher__user=request.user)` with subject, group, student count, schedule slots. Given a logged-in teacher, when opening `/panel/`, then only their classrooms are listed.
- [x] 4.2 Classroom detail view/template: subject, schedule slots, group members, session list (recent first), and a create-session form (`SessionCreateForm`: date) posted with `hx-post`, swapping the session list partial. Given the teacher picks an existing date, when submitting, then a validation error is shown and no duplicate is created; given a new date, then the session is created and the list updates in place.
- [x] 4.3 Session detail view/template: per-student status radios for all group members, `AttendanceFormSet` saving all records with `hx-post` and `hx-target` on the student-list partial plus a success flash. Given changed statuses, when the teacher saves, then records update and the partial re-renders without a full page reload.
- [x] 4.4 Wire `school/urls.py` and include it in `config/urls.py` under `panel/`. Given the URLs, when hitting `/panel/`, `/panel/classrooms/<id>/`, `/panel/sessions/<id>/`, then the correct views respond with permission checks.

## 5. Verification

- [x] 5.1 Run `uv run manage.py check`; fix any issues. Given the finished change, when `check` runs, then it reports no issues.
- [x] 5.2 Manual smoke test with dev data: create superuser, teacher user + Teacher, students, group, subject, classroom with schedule; log in as teacher; create a session; mark statuses; verify records in admin. Given seeded data, when following the flows, then all scenarios from the specs behave as specified.
