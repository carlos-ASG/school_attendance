## 1. Design-system components

- [x] 1.1 Given the lucide `image-off` SVG, create `src/core_ui/templates/cotton/icon/image_off.html` following the existing per-icon template pattern (raw SVG + `{{ attrs }}` passthrough)
- [x] 1.2 Create `src/core_ui/templates/cotton/student_photo.html` cotton component with `src` and `alt` props: when `src` is set render an `<img>` with rounded object-cover Tailwind classes; otherwise render a same-sized placeholder with `<c-icon.image_off />` centered
- [x] 1.3 Run `uv run manage.py tailwind build` so the new utility classes are present in the prebuilt CSS

## 2. View and URL

- [x] 2.1 Create `src/teacher_panel/views/student_detail.py` with `StudentDetailView(TeacherRequiredMixin, DetailView)`: resolve the course via `get_object_or_404(..., pk=kwargs['course_pk'], teacher=self.teacher)` and the student via `get_object_or_404(Student, pk=kwargs['pk'], student_groups=course.student_group)`; compute `attendance` context (attended = `PRESENT`/`LATE`/`EXCUSED` count via one aggregate, total = `course.sessions.count()`, percentage formatted `{:.1f}`, `0/0 (0)` when no sessions) importing `ATTENDED_STATUSES` from `views/course_detail.py`; context also carries `course` and `student`
- [x] 2.2 Export `StudentDetailView` from `src/teacher_panel/views/__init__.py` and add URL `path('courses/<uuid:course_pk>/students/<uuid:pk>/', ..., name='course_student_detail')` to `src/teacher_panel/urls.py`
- [x] 2.3 Verify with `uv run manage.py check`

## 3. Templates

- [x] 3.1 Create `src/teacher_panel/templates/teacher_panel/student_detail.html` extending `teacher_panel/base.html`: breadcrumb Home → course subject → student full name; `c-layout.surface` header with `<c-student_photo>` (passing `student.photo.url` only when `student.photo`) and the student's name; a "Datos personales" card using `c-detail_list` (nombre, apellido paterno, apellido materno, correo, grupo); an "Asistencia en el curso" card showing `attended/total (percentage%)`; Spanish copy throughout
- [x] 3.2 In `src/teacher_panel/templates/teacher_panel/course_detail.html`, wrap each student name in the student list with `<c-quiet_text href="{% url 'teacher_panel:course_student_detail' course.pk row.student.pk %}">` via `<c-slot name="label">`, leaving the attendance value column unchanged
- [x] 3.3 Rebuild Tailwind (`uv run manage.py tailwind build`) after template edits

## 4. Tests

- [x] 4.1 Add `StudentDetailViewTests` in `src/school/tests.py`: teacher opens own course's student → 200, page contains the student's name and `attended/total (percentage%)`; student with photo → response contains `/media/`; student without photo → response contains the image-off fallback markup and no `/media/`
- [x] 4.2 Add denial tests: teacher requests the page via another teacher's course → 404; student not in the course's group → 404; course with no sessions shows `0/0 (0%)`
- [x] 4.3 Run the full test suite (`uv run manage.py test`) and confirm `TeacherPanelPhotoExclusionTests` still pass untouched
