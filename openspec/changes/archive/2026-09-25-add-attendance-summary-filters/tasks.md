# Tasks — add-attendance-summary-filters

## 1. Selector con cotas de fecha

- [x] 1.1 Extender `get_course_attendance_summary` en `src/school/selectors/attendance.py` con `date_from=None, date_to=None` (keyword-only): construir un dict de filtros `date__gte`/`date__lte` y `session__date__gte`/`session__date__lte` solo con las cotas presentes y aplicarlo al denominador (`course.sessions.filter(...)`) y al numerador (`AttendanceRecord`). Sin parámetros, comportamiento idéntico al actual.
- [x] 1.2 Tests en `tests/school/test_attendance_selectors.py`: rango completo acota numerador y denominador; solo `date_from` (cota superior abierta); solo `date_to`; rango de un solo día; rango sin sesiones devuelve `0/0 (0%)` por estudiante; sin parámetros = paridad con el resultado actual.

## 2. Formulario de filtros

- [x] 2.1 Crear `AttendanceSummaryFilterForm` en `src/teacher_panel/forms.py`: campos opcionales `date_from`/`date_to` (`DateField`, `required=False`, labels en español "Desde"/"Hasta") y `clean()` que rechace `date_from > date_to` con error en español.

## 3. Vista y ruta

- [x] 3.1 Crear `CourseAttendanceSummaryView` en `src/teacher_panel/views/course_attendance_summary.py` (`TeacherRequiredMixin`): resolver el curso con `get_object_or_404(teacher_courses(teacher=self.teacher), pk=...)`; en `get()`, bindear `AttendanceSummaryFilterForm(request.GET)`; si es válido, `attendance = get_course_attendance_summary(course, **cleaned)`; si no, contexto con el form y sus errores sin consulta de resumen. Con `request.htmx` responder `render(request, "teacher_panel/course_attendance_summary.html#attendance_summary", context)`; sin HTMX, página completa. Exportar en `views/__init__.py`.
- [x] 3.2 Registrar la ruta `courses/<uuid:pk>/attendance/` (name `course_attendance_summary`) en `src/teacher_panel/urls.py`.

## 4. Template de la página

- [x] 4.1 Crear `src/teacher_panel/templates/teacher_panel/course_attendance_summary.html` (extiende `teacher_panel/base.html`): breadcrumb Inicio → Curso → Resumen de asistencia; header con subject y grupo; form `method="get"` con `hx-get` a la misma URL, `hx-trigger="submit"`, `hx-target="#attendance-summary"`, `hx-swap="outerHTML"`, `hx-push-url="true"`, inputs `name="date_from"/"date_to"` inicializados con los valores del form, botón "Filtrar" y control para limpiar.
- [x] 4.2 Definir `{% partialdef attendance_summary inline %}` dentro de `#attendance-summary`: errores del form, tabla `c-detail_list` (o `c-table`) con Estudiante → `attended/total (percentage%)` enlazando cada estudiante a `course_student_detail`, y estados vacíos ("No hay estudiantes" / "No hay sesiones en este rango" cuando el total del rango es 0). Correr `uv run manage.py tailwind build` tras añadir clases nuevas.

## 5. Entrada desde el detalle del curso

- [x] 5.1 En `course_detail.html`, añadir junto a "Historial de sesiones" un `c-button` variant="outline" "Resumen de asistencia" con `href` a la nueva ruta (icono coherente, p. ej. `c-icon.chart` si existe).

## 6. Tests de vista

- [x] 6.1 Crear `tests/teacher_panel/test_course_attendance_summary.py`: GET sin parámetros muestra resumen acumulado; GET con `date_from`/`date_to` aplica el rango (fixture con sesiones en varias fechas); HTMX GET (`HTTP_HX_REQUEST`) responde solo el fragmento (sin base chrome, contiene `hx-` target id); GET de curso ajeno → 404; anónimo → redirect a login; `from > to` → error visible y sin tabla de datos; URL con query sin HTMX renderiza página completa filtrada.

## 7. Verificación

- [x] 7.1 `uv run manage.py check` en verde.
- [x] 7.2 `uv run pytest` completo en verde.
- [x] 7.3 Recorrido manual con `uv run manage.py runserver`: filtrar rango, rango de un día, limpiar filtros, back button tras `hx-push-url`, recargar URL filtrada.
