- [ ] agregar mensaje de error al tratar de cambiar la fecha a una que ya tiene una sesion
- [X] evitar que se pueda editar una sesion de un curso de un ciclo que ya paso
- [x] deshabilitar toma de asistencia para el dia de hoy en una fecha fuera de los dias asginados al curso, por ejemplo si tu horario son. los lunes y martes y hoy es miercoles directamente no deberia dejarte tomar asistencia
- [ ] agregar los campos que faltan a el sidebar de unfold
- [ ] cambiar mensaje de error "Para la sesión de hoy, usa la tarjeta "Sesión de hoy"" para el model historial de sesion.
- [ ] ajustar card de sesion en el template de course_detail.html
- [ ] hay un bug al cambiar de tema cuando vas al dashboard desde el sidebar, creo que internamente en alpine si se cambia el estado del tema pero no se refleja en la pantalla, porque cuando navegas a cualquier otra pagina si se cambia el tema. me acabo de dar cuenta que solo ocurre con el tema oscuro, si navegas a cualquier pagina con el tema oscuro activo hay un error que evita que se refresque de forma reactiva el tema, si cambia cuando navegas a otro ruta, pero en la pagina que estas si empiezas con el tema oscuro falla con la reactividad.
- [ ] agregar capacidad de cargar el calendario de dias inhabil con un excel/csv asi como el padron de alumno
- [ ] encontrar un mejor lugar para el historial de otros curso del dashboard (considerar un template aparte)
- [ ] agregar conexion a nierka con apikey
- [ ] ver que pasa si hay discrepacia de credenciales entre nierika y PACE, que pasa si se extiende o revoca una credenciales que PACE no tiene registrada?
- [ ] Implementar soporte de zonas horarias
- [ ] implementar soporte para clases de ayuda fuera de horario de clase que no tengas repercusiones con la asistencia normal
- [ ] revisar test_credential_events.py

- [ ] Agregar iconos al lado de los titulos de las cards

- capacidad para configurar fecha maxima de expiracion de credencial en un rango de 3 a 5 años