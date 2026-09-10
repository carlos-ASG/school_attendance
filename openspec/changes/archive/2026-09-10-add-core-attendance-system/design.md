## Context

Fresh Django 6.1 project (`config/` settings package, SQLite, no apps). Tech stack: Python, Django, HTMX — the teacher panel is server-rendered templates with HTMX for partial updates. Admins manage reference data through Django admin; teachers never touch Django admin.

## Goals / Non-Goals

**Goals:**
- Core domain models: Student, Teacher, Subject, StudentGroup, Classroom, AttendanceSession, AttendanceRecord.
- Classroom = one StudentGroup + one Teacher + one Subject + a schedule; same Teacher/Subject pair may repeat across different groups and schedules.
- Attendance sessions created by the classroom's teacher; per-student records with statuses.
- Django admin CRUD for all entities; custom HTMX teacher panel (login, classroom list, session creation, attendance recording).

**Non-Goals:**
- Schedule conflict validation (teacher/group double-booking), timetable generation.
- Reports, analytics, absence notifications, REST API, student/parent logins.

## Decisions

1. **Single app `school`** — all domain models in one Django app at repo root. Alternatives (split apps per entity) add ceremony with no benefit at this size.

2. **Teacher ↔ User via nullable OneToOne** — `Teacher.user` is `OneToOneField(User, null=True, blank=True, unique when set)`. Admins can create Teacher records before accounts exist; panel access requires the link. Names live on `Teacher` (own fields), consistent with `Student`, avoiding divergence issues of deriving from `User`. Admins are plain Django `is_staff`/`is_superuser` users — no separate Admin model.

3. **`StudentGroup` as explicit model with M2M to Student** — groups are reusable, named, and managed independently, so a group can appear in multiple classrooms (e.g., same group, different subjects).

4. **Classroom schedule as `ClassSchedule` slots** — a Classroom has a *set* of slots (`weekday`, `start_time`, `end_time`) representing its one schedule (e.g., Mon+Wed 10:00–11:30). Beats a text field (queryable, validated) and beats single columns on Classroom (multi-day classes). Uniqueness of a Classroom: `unique_together (teacher, subject, student_group)` — same teacher+subject with the same group is the same classroom (its slots carry the times); different group or different slots ⇒ different classroom, satisfying "same teacher, same subject, different group and schedule".

5. **Sessions: `unique_together (classroom, date)`**, FK `created_by` → Teacher, plus `created_at` and optional `notes`. Creating a session auto-generates one `AttendanceRecord` per student in the classroom's group, defaulting to `PRESENT` (fastest UX: mark the absentees). Statuses: `PRESENT / ABSENT / LATE / EXCUSED`; `unique_together (session, student)`. Records stay editable (no finalize/close state — YAGNI).

6. **Permissions**: only the classroom's teacher (or a staff user) can create sessions for it; the panel only ever queries `Classroom.objects.filter(teacher__user=request.user)`. Admins manage everything via Django admin.

7. **Panel routes** under `/panel/`: dashboard (classroom list), `classrooms/<id>/` (detail + create session), `sessions/<id>/` (attendance form). Auth via Django `LoginView`/`LogoutView` at `/panel/login/`, `/panel/logout/`. Post-login redirect: staff → `/admin/`, teacher → `/panel/`; root `/` redirects accordingly. Attendance editing is a plain POST form of per-student radio inputs; HTMX (`hx-post` on the form, `hx-target` the student list partial) swaps the updated list with a success flash — one request per save, no per-row complexity.

8. **HTMX vendored** — download `htmx.min.js` once into `school/static/school/js/htmx.min.js` and reference it in `base.html`. No CDN dependency at runtime, no JS build tooling. Minimal hand-written CSS in a single static file; no CSS framework.

9. **Admin**: `ModelAdmin` registrations with `list_display`/`list_filter`, `filter_horizontal` for group students, `ClassSchedule` inline on Classroom, `AttendanceRecord` inline on AttendanceSession.

## Risks / Trade-offs

- [No schedule-conflict validation: a teacher/group can be double-booked] → Accept for now; admin's responsibility; noted as future validation.
- [Default PRESENT: teacher may forget to mark absentees] → Accepted trade-off for fast recording; records editable afterward.
- [(classroom, date) uniqueness forbids two same-day sessions (double periods)] → Accepted; keep one session per classroom-day; revisit if needed.
- [Teacher names on Teacher, not User, can drift from login name] → Panel always shows Teacher fields; acceptable.
- [Vendored htmx can go stale] → Pin the version, trivially updatable.

## Migration Plan

1. Create app + models, `makemigrations school`, `migrate` (SQLite, no existing domain data — nothing to roll back; the db only has Django's default tables).
2. Add admin registrations, views/templates, URLs — no schema impact.
