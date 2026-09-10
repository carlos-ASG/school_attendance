## Why

The project is a fresh Django skeleton with no domain apps. We need the core school attendance system: the academic entities (Student, Teacher, Subject), classroom groupings with schedules, attendance sessions created by teachers, and role separation between Admins (Django admin) and Teachers (custom panel).

## What Changes

- Add a Django app (`school`) containing the core domain models:
  - `Student` (person, not a login user)
  - `Teacher` (linked one-to-one with a Django `User` so teachers can log in)
  - `Subject`
  - `StudentGroup` (named group of students, reusable across classrooms)
  - `Classroom` (one StudentGroup + one Teacher + one Subject + one schedule; the same Teacher may teach the same Subject in multiple classrooms differing by group and/or schedule)
  - `AttendanceSession` (created by the classroom's teacher for a given date)
  - `AttendanceRecord` (per-student attendance status within a session)
- Register all entities in Django admin with useful list views/filters for Admin users.
- Build a custom teacher panel (Django templates + HTMX): login, list of the teacher's classrooms, create attendance sessions, and record per-student attendance.
- Migrations for all new models (SQLite).

## Capabilities

### New Capabilities
- `academic-structure`: Models and admin management for Students, Teachers (linked to login users), Subjects, Student Groups, and Classrooms (group + teacher + subject + schedule, allowing repeated teacher/subject pairs with different groups/schedules).
- `attendance-tracking`: Attendance sessions per classroom created by the classroom's teacher, and per-student attendance records with statuses (present / absent / late / excused).
- `teacher-panel`: Custom HTMX panel for teacher users: authentication, viewing their classrooms, creating sessions, and recording/editing attendance for a session.

### Modified Capabilities

(none — no existing specs)

## Impact

- New app `school/` (models, admin, forms, views, urls, templates, migrations).
- `config/settings.py`: add `school` to `INSTALLED_APPS`; login/logout URLs.
- `config/urls.py`: include teacher panel routes.
- Database: new tables, SQLite via Django migrations.

## Non-goals

- No student/parent portal or self-service login.
- No automated scheduling, timetable generation, or calendar UI.
- No reports/analytics or attendance statistics dashboards.
- No REST API — the teacher panel is server-rendered with HTMX.
- No email notifications for absences.
