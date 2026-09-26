## Context

El resumen de asistencia por curso hoy vive en `course_detail.html` y usa `get_course_attendance_summary(course)` (`src/school/selectors/attendance.py:11`): denominador = todas las sesiones del curso, numerador = registros con estado en `ATTENDED_STATUSES` (PRESENT, LATE, EXCUSED). No hay forma de acotar por fechas.

El repo ya tiene el patrón HTMX/Django 6 a seguir (referencia: `course_session_history`): fragmentos `{% partialdef %}` dentro de la página que los renderiza, la vista detecta `request.htmx` y responde `render(request, "page.html#fragment", context)`, con fallback sin JS (página completa / redirect). El detalle por día ya existe en las páginas de sesión, así que esta página solo necesita el filtro de rango.

## Goals / Non-Goals

**Goals:**

- Página `courses/<pk>/attendance/` con resumen por estudiante acotable por rango de fechas.
- Filtrado HTMX sin recarga completa, con URL compartible (`hx-push-url`).
- Mantener el patrón de queries del selector (≤ 2 queries).

**Non-Goals:**

- Vista de estados por día (ya cubierta por `today_session_detail` / `previous_session_detail`).
- Presets por ciclo, exportes, paginación, ordenamiento.
- Cambiar los resúmenes existentes (detalle de curso y de estudiante siguen acumulados).

## Decisions

### D1 — Un solo filtro de rango, campos opcionales y sin cotas

`date_from` y `date_to` opcionales: vacío = sin cota en ese extremo. Un rango de un día es `date_from == date_to`. Alternativa descartada: modo "día específico" separado — duplicaría el caso degenerario del rango y el detalle fino ya está en las páginas de sesión.

- Default (ambos vacíos) = acumulado total, idéntico al card del detalle del curso: no hace falta decidir default por ciclo y el estado inicial es predecible.

### D2 — Extender el selector existente, no crear uno nuevo

`get_course_attendance_summary(*, course, date_from=None, date_to=None)`: construir `filters` dict con `session__date__gte` / `session__date__lte` solo para cotas presentes y aplicarlo tanto a `course.sessions.filter(**...)` (denominador) como a `AttendanceRecord.objects.filter(session__course=course, ...)` (numerador). Sin parámetros el comportamiento es byte-igual al actual (compatibilidad con `CourseDetailView` y `StudentDetailView`, sin tocarlos).

Alternativa descartada: selector nuevo `get_course_attendance_summary_between` — duplica la fórmula y el cálculo de porcentaje, dos sitios que desincronizar.

### D3 — GET + form sobre la misma URL, fragmento con `partialdef`

- Ruta única `courses/<pk>/attendance/` (`CourseAttendanceSummaryView`); el formulario hace `hx-get` sobre sí misma con `hx-trigger="submit"`, `hx-target="#attendance-summary"`, `hx-swap="outerHTML"`, `hx-push-url="true"`.
- El template define `{% partialdef attendance_summary inline %}` (tabla + estado vacío + errores de validación dentro del fragmento) para que el swap reemplace todo lo dependiente del filtro.
- Vista: `FormView`-style GET — bindea `AttendanceSummaryFilterForm(request.GET)`; si es válido computa el resumen, si no re-renderiza con errores. Si `request.htmx` → `render(request, "teacher_panel/course_attendance_summary.html#attendance_summary", context)`; si no → página completa. GET no requiere CSRF.
- `from > to` → error de form (`clean()` que compara ambas cuando ambas vienen), se re-renderiza el fragmento con el error — sin `retarget` porque el target del form ya es el contenedor del fragmento.
- Trigger por botón (submit), no por `change`: predecible en tablet; sin debounce que dispare a mitad de teclear.

### D4 — Vista en módulo propio, misma convención que el resto

`src/teacher_panel/views/course_attendance_summary.py` con `CourseAttendanceSummaryView` (page view; el fragmento sale del mismo GET), exportada en `views/__init__.py`, ruta `attendance/` en `urls.py`, form en `forms.py`. Acceso: `get_object_or_404(teacher_courses(teacher=...), pk=kwargs["pk"])` (mismo guard que `CourseSessionHistoryView.get_course`). Template plano `teacher_panel/course_attendance_summary.html`, breadcrumb Inicio → Curso → Resumen de asistencia, botón de entrada en `course_detail.html` junto a "Historial de sesiones", estudiante enlazado a su detalle (como en el card actual).

### D5 — Semántica del porcentaje dentro del rango

Denominador = sesiones del curso con fecha en el rango; numerador = registros del estudiante en esas sesiones con `ATTENDED_STATUSES`. Estudiantes sin registros en el rango (p. ej. ingresados después) muestran `0/N`. Rango sin sesiones → `0/0 (0%)` con estado vacío informativo. Misma fórmula y formato (`x/y (zz.z%)`) que el resto del panel.

## Risks / Trade-offs

- [Rango sin sesiones muestra puros ceros] → estado vacío con mensaje "No hay sesiones en este rango" en lugar de una tabla engañosa.
- [`hx-push-url` deja query params en la URL al navegar de vuelta desde otra página] → comportamiento deseado (shareable/back); el query solo afecta a esta ruta.
- [Fecha futura en el filtro] → inofensivo: no hay sesiones futuras (la creación de sesiones valida fecha ≤ hoy); el rango simplemente no aporta sesiones. No se valida.
- [Divergencia de fórmula con el card del detalle] → misma función selector con parámetros default; tests de paridad incluidos.

## Migration Plan

Sin migraciones ni datos. Despliegue: solo código (urls, vistas, templates, forms, selector). Rollback: revertir el commit; el detalle del curso nunca deja de funcionar porque no se modifica.

## Open Questions

(ninguna — resueltas en exploración: sin modo día, default acumulado, trigger por botón, push-url activado)
