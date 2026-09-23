## Why

Teachers currently see only a flat attendance summary per student on the course detail page; they cannot inspect an individual student. A course-scoped student detail page gives the teacher the student's photo, personal data, and attendance average in that course, without exposing students from other teachers' courses.

## What Changes

- New teacher-panel page at `courses/<uuid:course_pk>/students/<uuid:pk>/` (`course_student_detail`) showing the student's photo, personal data (full name, email, group), and their attendance average in that course.
- The course detail page's student list links each student's name to the new page via the `quiet_text` component.
- Access denial: a teacher requesting a student through a course they do not teach, or a student outside the course's group, gets a 404.
- New `image_off` icon component and a new `student_photo` cotton component that renders the photo when present, or a centered `image_off` icon as fallback.
- **Spec amendment**: the `student-photos` spec currently forbids displaying photos anywhere in the teacher panel; it gains an exception for the course student detail page.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `teacher-panel`: new requirement for the course student detail view (page contents, attendance average reuse, link from course detail student list, access denial scenarios).
- `student-photos`: modified requirement — photos remain excluded from the teacher panel except on the course student detail page.

## Impact

- `src/teacher_panel/urls.py`, `src/teacher_panel/views/` (new `student_detail` view), `src/teacher_panel/views/__init__.py`.
- `src/teacher_panel/templates/teacher_panel/student_detail.html` (new), `course_detail.html` (student list rows gain link).
- `src/core_ui/templates/cotton/icon/image_off.html` (new), `src/core_ui/templates/cotton/student_photo.html` (new); requires Tailwind rebuild (`uv run manage.py tailwind build`).
- `src/school/tests.py`: new tests for the page (photo shown, icon fallback, 404 denials); existing `TeacherPanelPhotoExclusionTests` remain untouched.

## Non-goals

- Per-session attendance history on the student detail page (explicitly deferred).
- Editing student data or photos from the teacher panel (admin-only).
- Global (non-course-scoped) student pages or cross-course attendance averages.
