## Context

The teacher panel course detail page (`src/teacher_panel/templates/teacher_panel/course_detail.html`) lists each student of the course's group with an attendance summary computed by `CourseDetailView.get_attendance_summary()` (src/teacher_panel/views/course_detail.py:40). The `student-photos` spec currently forbids displaying student photos anywhere in the teacher panel (enforced by `TeacherPanelPhotoExclusionTests` in src/school/tests.py:834). Design-system patterns: cotton components in `src/core_ui/templates/cotton/` (one file per icon under `cotton/icon/`, `{{ attrs }}` passthrough), page templates extend `teacher_panel/base.html` with `c-layout.surface` + `c-card` + `c-detail_list`, all panel copy in Spanish.

## Goals / Non-Goals

**Goals:**

- Course-scoped student detail page at `courses/<uuid:course_pk>/students/<uuid:pk>/` with photo, personal data, and course attendance average.
- Link each student name in the course detail student list to the new page using the existing `quiet_text` component.
- Strict access denial (404) for teachers who don't own the course or students outside the course's group.
- Fallback UI (centered `image_off` icon) when the student has no photo.

**Non-Goals:**

- Per-session attendance history on the page (deferred).
- Editing student data/photos from the panel; global student pages; cross-course averages.

## Decisions

1. **Course-scoped URL over global `students/<pk>/`.** The attendance average is defined per course (sessions of that course as denominator), and the access rule (teacher owns course AND student in course group) maps directly onto the two URL parameters. A global page would need an ambiguous "average across the teacher's courses" definition and an indirect permission check. Alternative rejected: global page with course picker — bigger feature, no current need.

2. **View shape: `DetailView` on `Student` with the course resolved from kwargs.** `StudentDetailView(TeacherRequiredMixin, DetailView)` fetches the course with `get_object_or_404(Course.objects..., pk=kwargs['course_pk'], teacher=self.teacher)` (teacher scoping doubles as the access check, matching the `course__teacher=self.teacher` pattern used across the panel), then `get_object_or_404(Student, pk=kwargs['pk'], student_groups=course.student_group)` (M2M `Student.student_groups`). Any mismatch yields 404 — the established denial pattern in this panel. Context provides `course`, `student`, and `attendance` (attended/total/percentage).

3. **Reuse the exact attendance formula.** Attended statuses `PRESENT`, `LATE`, `EXCUSED` counted via one `AttendanceRecord` aggregate over `session__course=course, student=student`, divided by `course.sessions.count()` × 100, formatted `{:.1f}` — identical to `CourseDetailView.get_attendance_summary` and the spec'd "Course detail attendance calculation" requirement. Shows `0/0 (0%)` when the course has no sessions. (Two queries; no need to extract a shared helper for one extra call site, but constants stay importable from `course_detail.py` to keep a single source of truth for `ATTENDED_STATUSES`.)

4. **Photo rendering: new `c-student_photo` cotton component.** Props: `src`, `alt`. Renders `<img>` with rounded/cover Tailwind classes when `src` is set; otherwise a same-sized placeholder with `<c-icon.image_off />` centered. New `cotton/icon/image_off.html` follows the existing per-icon template pattern (raw lucide SVG + `{{ attrs }}`). Alternative rejected: inline conditional markup in the page template — duplicated when the page later grows, and the fallback placeholder is a design-system concern.

5. **Link injection via `label_slot`.** `c-detail_list.item` already exposes a `label` named slot; the course detail rows wrap the student name in `<c-quiet_text href="{% url 'teacher_panel:course_student_detail' course.pk row.student.pk %}">` inside `<c-slot name="label">`, leaving the value column unchanged. No component changes needed.

6. **Page layout follows panel conventions.** `student_detail.html` extends `teacher_panel/base.html`; breadcrumb Home → course subject → student full name; `c-layout.surface` header with photo + name, one card for personal data (`c-detail_list`: nombre, apellidos, correo, grupo), one card for the attendance average in the established `attended/total (percentage%)` format. All copy in Spanish.

## Risks / Trade-offs

- [Spec conflict with `student-photos`] → Handled explicitly: the change carries a MODIFIED delta for `student-photos` narrowing the exclusion to "every teacher-panel page except the course student detail page". Existing `TeacherPanelPhotoExclusionTests` only cover dashboard, course detail, and session pages, so they remain green without edits.
- [Photo page enables teacher enumeration of arbitrary students] → Mitigated by the double-scoped 404 (course ownership + group membership); no student data leaks outside the teacher's own courses.
- [New Tailwind utility classes silently dropped by stale prebuilt CSS] → Task includes `uv run manage.py tailwind build` after template work, per repo convention.
- [`student.photo.url` on empty field raises] → Component only renders `<img>` when `src` is provided; view/template never call `.url` on a falsy photo.
