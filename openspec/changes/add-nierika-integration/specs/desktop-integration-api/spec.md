# Spec Delta — desktop-integration-api

## ADDED Requirements

### Requirement: Padrón completo de estudiantes para el escritorio
El sistema SHALL exponer `GET /api/desktop/students` autenticado por API key del escritorio, que devuelva todos los estudiantes con `id`, `first_name`, `paternal_surname`, `maternal_surname`, `email`, la lista de nombres de sus grupos, `has_photo` y `photo_url` (ruta del endpoint de foto, nula si no tiene foto).

#### Scenario: Descarga del padrón
- **WHEN** el escritorio solicita `/api/desktop/students` con una key válida
- **THEN** recibe la lista completa de estudiantes con sus campos y grupos

#### Scenario: Sin autenticación no hay padrón
- **WHEN** se solicita el endpoint sin header `X-API-Key` o con key inválida
- **THEN** la respuesta es 401 genérico

### Requirement: Fotografía de estudiante servida por endpoint protegido
El sistema SHALL exponer `GET /api/desktop/students/{id}/photo` autenticado por la misma API key, que devuelva los bytes de la fotografía con content-type apropiado. Las fotos NO se expondrán por URL pública de media.

#### Scenario: Descarga de foto existente
- **WHEN** el escritorio solicita la foto de un estudiante que tiene fotografía
- **THEN** recibe los bytes de la imagen con `image/jpeg`

#### Scenario: Estudiante sin foto
- **WHEN** se solicita la foto de un estudiante sin fotografía
- **THEN** la respuesta es 404

### Requirement: Notificación push de credencial emitida con relación estudiante
El sistema SHALL exponer `POST /api/desktop/credential-events` que acepte eventos `{operation: "issued", occurred_at, credential: {id, serial_number, issued_at, expiration_date, max_expiration_date, scan_kind}, student_id}`. El evento SHALL aplicarse transaccionalmente: upsert de la credencial en el espejo y creación de la relación estudiante-credencial. El evento SHALL ser idempotente (reenvío del mismo evento no duplica ni altera el resultado final).

#### Scenario: Emisión crea credencial y relación
- **WHEN** llega un evento `issued` con una credencial nueva y un `student_id` válido
- **THEN** la credencial queda en el espejo y existe una relación activa entre ese estudiante y esa credencial

#### Scenario: Reemisión cierra la relación anterior
- **WHEN** un estudiante con relación activa a la credencial A recibe un evento `issued` de la credencial B
- **THEN** la relación con A queda cerrada (historial preservado) y la activa pasa a ser B

#### Scenario: Reenvío idempotente
- **WHEN** el mismo evento `issued` se recibe dos veces
- **THEN** el resultado es idéntico a recibirlo una vez (una credencial, una relación activa)

#### Scenario: Estudiante inexistente
- **WHEN** llega un evento `issued` con un `student_id` que no existe
- **THEN** la respuesta es 422 con error de validación y no se persiste nada

### Requirement: Notificación push de revocación y extensión de vigencia
El sistema SHALL aceptar en el mismo endpoint eventos `{operation: "revoked", occurred_at, credential_id, revoked_at}` que fijen `revoked_at` de la credencial y cierren su relación activa, y `{operation: "validity_extended", occurred_at, credential_id, expiration_date, max_expiration_date}` que actualicen las vigencias del espejo.

#### Scenario: Revocación actualiza espejo y cierra relación
- **WHEN** llega un evento `revoked` para una credencial con relación activa
- **THEN** la credencial refleja `revoked_at` y la relación queda cerrada

#### Scenario: Extensión de vigencia actualiza el espejo
- **WHEN** llega un evento `validity_extended` con nuevas fechas
- **THEN** la credencial refleja las vigencias actualizadas

#### Scenario: Evento sobre credencial desconocida
- **WHEN** llega un evento `revoked` o `validity_extended` cuyo `credential_id` no existe en el espejo
- **THEN** la respuesta es 404 y no se persiste nada

### Requirement: Operación desconocida rechazada
El endpoint de eventos SHALL rechazar con 422 cualquier `operation` distinta de `issued`, `revoked` o `validity_extended`.

#### Scenario: Operation inválida
- **WHEN** llega un evento con `operation: "deleted"`
- **THEN** la respuesta es 422 indicando operación no soportada

### Requirement: Coexistencia con la API de profesores
El router de escritorio SHALL montarse en el mismo `NinjaAPI` existente sin alterar la operación ni la autenticación de `PATCH /api/sessions/{session_id}/records` (sesión de profesor con CSRF). Las claves de ruta SHALL estar bajo el prefijo `/api/desktop/` para no colisionar con rutas futuras.

#### Scenario: API de asistencia intacta
- **WHEN** se ejecuta la suite de tests existente de `src/api` tras el cambio
- **THEN** todos los tests de `update_session_records` siguen pasando sin modificación
