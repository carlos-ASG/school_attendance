## Context

The `school` app currently owns both the domain model/admin layer and the teacher-facing panel. The panel already supports login, dashboard, classroom detail, session creation, and attendance editing, but it lives inside `school` and lacks session edit/delete. Meanwhile, the Django admin allows an `AttendanceRecord` to reference any `Student` because the `AttendanceRecordInline` has no queryset or model-level guard.

This change splits the teacher UI into a dedicated `teachers` app, renames the overloaded `Classroom` model to `Course`, moves session notes to per-record notes, adds `updated_at` tracking, and hardens student-membership validation.

## Goals / Non-Goals

**Goals:**
- Extract all teacher-facing views, forms, templates, and URLs from `school` into a new `teachers` app served under `/teacher/`.
- Rename `Classroom` → `Course` and add a `classroom` physical-room field.
- Remove `notes` from `AttendanceSession`; add optional `notes` to `AttendanceRecord`.
- Add `updated_at` to `AttendanceSession`, `AttendanceRecord`, and `Course` using Django's `auto_now=True` (null until first update).
- Prevent attendance records from referencing students outside the session's course group via form scoping and `AttendanceRecord.clean()`.
- Add `django-htmx` for partial-page updates in the teacher panel.
- Pre-load a read-only admin Django group.
- Add tests for the membership validation.

**Non-Goals:**
- No public API or mobile interface.
- No database triggers for `updated_at`.
- No new reporting or analytics.
- No database-trigger-level validation.

## Decisions

### 1. Split `school` into domain (`school`) and teacher UI (`teachers`)

```
school/                 teachers/
├── models.py           ├── views.py
├── admin.py            ├── forms.py
├── migrations/         ├── urls.py
├── resources.py        └── templates/teachers/
└── templates/admin/        ├── base.html
                            ├── login.html
                            ├── dashboard.html
                            ├── course_detail.html
                            ├── session_detail.html
                            └── partials/
```

`teachers` imports models from `school`. This keeps admin configuration and domain logic in one place while giving the panel its own namespace, URL prefix, and templates.

### 2. Rename `Classroom` → `Course`

`Classroom` is overloaded: it represents a teacher/subject/group offering while "classroom" also sounds like a physical room. Renaming to `Course` lets the physical room be a `classroom` CharField on `Course`.

Migration strategy:
- `RenameModel(Classroom, Course)`
- `RenameField` on FKs that currently point to `Classroom`: `AttendanceSession.classroom → AttendanceSession.course`, `ClassSchedule.classroom → ClassSchedule.course`.
- Update related_names (`classrooms → courses`).
- Update all code references (admin, views, forms, templates).

### 3. Notes move from session to record

Teachers take notes per student (absence reason, justification, etc.), not per session. `AttendanceSession.notes` is dropped; `AttendanceRecord.notes` is added as `TextField(blank=True, default="")`.

### 4. `updated_at` via `auto_now=True, null=True`

```python
updated_at = models.DateTimeField(
    'Última actualización', auto_now=True, null=True, blank=True
)
```

`auto_now` fires on every `.save()` and keeps the field `NULL` until the first update. It does not fire on `queryset.update()` or `bulk_update()`, which is acceptable for current flows. A future performance-sensitive path can explicitly update the field.

### 5. Defense-in-depth validation for student membership

Two layers:

1. **Admin inline form scoping**: override `formfield_for_foreignkey` in `AttendanceRecordInline` so the `student` dropdown only lists members of `session.classroom.student_group`.
2. **Model validation**: `AttendanceRecord.clean()` raises `ValidationError` if `student` is not in `session.classroom.student_group`.

```
Admin save path:
  form choices  → limited to group students
  full_clean()  → model.clean() rejects outsiders
```

This covers the current bug without needing a database trigger. Bulk creation remains safe because `create_attendance_records()` only uses the course's group.

### 6. `django-htmx` integration

- Add `django-htmx` to dependencies, `INSTALLED_APPS`, and `MIDDLEWARE` (`HtmxMiddleware`).
- Load `{% htmx_script %}` in the panel base template and set `hx-headers='{"x-csrftoken": "{{ csrf_token }}"}'` on `<body>`.
- Views use `request.htmx` to render partial templates for htmx requests and full pages for direct requests.
- POST successes return partials that replace the relevant fragment; errors use `django_htmx.http.retarget()` to re-render the form in place.
- Redirects after htmx POSTs use `HttpResponseClientRedirect`.

### 7. Read-only admin group

A data migration creates a group named `Administradores de solo lectura` with view-only permissions on all `school` models. Superusers still have full access; membership in this group gives read-only access through the Django admin for back-office staff who should not mutate data.

### 8. URL paths

The teacher panel moves from `/school/` to `/teacher/`. Paths are renamed to match the `Course` model:

- `/teacher/` → dashboard
- `/teacher/courses/<pk>/` → course detail
- `/teacher/sessions/<pk>/` → session detail

Old `/school/` URLs can be dropped (dev environment) or redirected later if needed.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| `Classroom` rename touches many files and templates; a missed reference breaks at runtime. | Grep for `Classroom`, `classroom`, and related_names; run `uv run manage.py check` and smoke-test admin + panel after every edit. |
| `auto_now=True` does not update on `queryset.update()` or `bulk_update()`. | Document the limitation; current flows use `.save()` and `bulk_create` (which sets `created_at` only). |
| URL change from `/school/` to `/teacher/` breaks existing bookmarks. | Acceptable in dev; add redirects only if users report the need. |
| Admin inline form scoping depends on `session` being available; adding a record to a session without a saved session may behave oddly. | Guard the queryset building so it falls back to an empty queryset when `session` is `None`. |
| `django-htmx` partial rendering can return the wrong template if `request.htmx` is misused. | Use a small helper or consistent `partial_template_name` convention in every view. |

## Migration Plan

1. Add `django-htmx` dependency and settings entries.
2. Create new `teachers` Django app scaffold.
3. Write model migration in `school`:
   - Rename `Classroom` → `Course`.
   - Rename FK fields `classroom` → `course` on `AttendanceSession` and `ClassSchedule`.
   - Add `Course.classroom` CharField with `default=""`.
   - Add `updated_at` fields.
   - Remove `AttendanceSession.notes`.
   - Add `AttendanceRecord.notes` with `default=""`.
4. Write data migration creating the read-only admin group.
5. Update `school/admin.py` for new model names and inline validation.
6. Move/copy views/forms/urls/templates from `school` to `teachers`, updating references.
7. Wire `teachers.urls` into `config.urls` under `/teacher/`; remove old `/school/` panel URLs.
8. Add `teachers` to `INSTALLED_APPS` and `pyproject.toml` `module-name`.
9. Add tests for `AttendanceRecord.clean()`.
10. Run `uv run manage.py makemigrations`, `migrate`, `check`, and smoke tests.

Rollback: restore from the SQLite backup taken before migration; revert code changes via git.

## Open Questions

1. Should old `/school/` panel URLs redirect to `/teacher/` temporarily, or can they be removed outright?
2. Should deleting a session require explicit confirmation in the UI, or rely on browser confirmation via `hx-confirm`?
3. Should the course detail page show the physical `classroom` field in the list/dashboard, or only on the detail page?
