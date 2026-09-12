## Why

The admin inline for attendance sessions currently allows recording any student, even one outside the session's classroom group, because validation only lives in the teacher-panel flow. At the same time, the teacher panel is embedded in the `school` app and lacks full session management (edit/delete) and django-htmx-backed reactivity. We need to harden validation and turn the teacher panel into a first-class, dedicated application.

## What Changes

- **BREAKING** Rename the `Classroom` model to `Course` and add a `classroom` CharField for the physical room.
- **BREAKING** Remove `notes` from `AttendanceSession`; add optional `notes` TextField to `AttendanceRecord` with `default=""`.
- Add `updated_at` DateTimeField to `AttendanceSession`, `AttendanceRecord`, and `Course` using Django's `auto_now=True` (null until first update).
- Extract the existing teacher-facing views, forms, templates, and URLs from `school` into a new `teachers` app under `/teacher/`.
- Add full AttendanceSession CRUD in the teacher panel: create, edit date, and delete sessions; keep attendance record editing.
- Harden validation so `AttendanceRecord.student` must belong to `session.classroom.student_group` via inline form scoping and `AttendanceRecord.clean()`.
- Add `django-htmx` for partial-page updates (session list, attendance table, inline forms).
- Add tests for the new student-membership validation.
- Pre-load a Django group for read-only admin users.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `teacher-panel`: extract to dedicated `teachers` app; add session edit/delete; use django-htmx for partial updates.
- `attendance-tracking`: move notes from session to record; add `updated_at`; enforce student-in-group validation.
- `academic-structure`: rename `Classroom` model to `Course`; add physical `classroom` field.

## Impact

- Database schema: renamed table, dropped `AttendanceSession.notes` column, new `classroom`, `notes`, and `updated_at` columns.
- URLs: `/teacher/` namespace replaces `/school/` for panel routes.
- Admin: continues to manage all entities; the AttendanceRecord inline is scoped to group students.
- Templates: moved/renamed from `school/` to `teachers/`.

## Non-goals

- No database triggers for `updated_at` (Django `auto_now=True` is used instead).
- No API or mobile interface.
- No gradebook or reporting changes.
- No database-trigger-level validation.
