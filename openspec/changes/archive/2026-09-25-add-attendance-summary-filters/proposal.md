## Why

La única vista del resumen de asistencia por curso está en la página de detalle del curso y es un acumulado de todas las sesiones. El profesor no puede responder preguntas como "¿cómo fue la asistencia en septiembre?" ni acotar el porcentaje a un periodo. La página de resumen necesita filtros de fecha.

## What Changes

- Nueva página `courses/<pk>/attendance/` con el resumen de asistencia por estudiante del curso, acotable por rango de fechas (`date_from` / `date_to`, ambos opcionales: vacío = sin cota; ambos vacíos = acumulado total, mismos números que el detalle del curso).
- Filtrado vía HTMX: el formulario de filtros hace `hx-get` sobre la misma URL y solo se re-renderiza el fragmento del resumen (`{% partialdef %}` + `template.html#partial`), con `hx-push-url` para que el rango quede en la URL (compartible, botón atrás).
- Validación `date_from > date_to` re-renderiza el fragmento con el error.
- Entrada: botón "Resumen de asistencia" en la página de detalle del curso, junto a "Historial de sesiones".
- El selector `get_course_attendance_summary` gana cotas de fecha opcionales (denominador: sesiones en el rango; numerador: registros asistidos en el rango).
- El detalle por día NO se construye aquí: las páginas de sesión existentes ya lo cubren; un rango de un día muestra `x/1 (…%)` y el detalle fino se consulta vía "Historial de sesiones".

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `teacher-panel`: nuevo requisito "Course attendance summary with date filters" (página, filtros opcionales, HTMX fragment + push-url, validación, acceso restringido al profesor del curso); el requisito "Course detail view" gana el enlace al resumen; el requisito "HTMX fragment responses render template partials" incorpora el swap del resumen filtrado a su lista.

## Impact

- **Selectores**: `src/school/selectors/attendance.py` — `get_course_attendance_summary(course, date_from=None, date_to=None)`; mantiene el patrón de dos queries.
- **Teacher panel**: nueva vista `src/teacher_panel/views/course_attendance_summary.py` + ruta en `urls.py` + formulario de filtros en `forms.py`; nuevo template `teacher_panel/course_attendance_summary.html`; botón de entrada en `course_detail.html`.
- **Tests**: extender `tests/school/test_attendance_selectors.py` (cotas de fecha) y crear tests de vista bajo `tests/teacher_panel/`.
- Sin cambios de modelos ni migraciones. Sin cambios rompientes: sin los parámetros, el selector se comporta igual que hoy.

## No objetivos

- No se construye una vista de estados por día (Presente/Ausente/…): ya existe en las páginas de sesión (`today_session_detail` / `previous_session_detail`).
- No se añaden filtros por ciclo escolar, presets ("este mes"), export CSV/PDF ni paginación.
- No se modifica el resumen acumulado de la página de detalle del curso ni el de la página de detalle de estudiante.
- No se filtra por estudiante ni se ordena por asistencia; el orden sigue siendo el del grupo.
