# Spec Delta — credential-mirror

## ADDED Requirements

### Requirement: Descarga completa del catálogo con upsert idempotente
El sistema SHALL proveer un management command (`sync_nierika_credentials`) que descargue el catálogo completo de credenciales del emisor desde `GET {NIERIKA_API_BASE_URL}/api/integrations/me/credentials` autenticado con header `X-API-Key: {NIERIKA_API_KEY}`, iterando páginas con el cursor compuesto `(createdAt, id)` hasta agotar el catálogo, y aplicando upsert por `id` de credencial en la tabla espejo local.

#### Scenario: Descarga paginada completa
- **WHEN** el emisor tiene más credenciales que el `limit` por página
- **THEN** el command solicita todas las páginas siguiendo el cursor devuelto por el servidor hasta `hasMore=false` y upserta cada credencial por su `id`

#### Scenario: Upsert idempotente en re-ejecuciones
- **WHEN** el command corre dos veces sin cambios en el catálogo
- **THEN** la segunda corrida actualiza las mismas filas (sin duplicados) y el resultado es idéntico

#### Scenario: Credencial existente actualizada por reconciliación
- **WHEN** una credencial local quedó desactualizada por un push perdido y el command la descarga con datos distintos
- **THEN** la fila local se actualiza con los datos del servidor

### Requirement: Sincronización condicionada a API key configurada
El command SHALL ser un no-op (exit code 0 con mensaje informativo, sin llamadas HTTP) cuando `NIERIKA_API_KEY` no esté configurada. SHALL lanzar error solo si la key está configurada pero la petición falla (red, 401, 5xx).

#### Scenario: Sin API key no hay llamadas
- **WHEN** `NIERIKA_API_KEY` no está definida en el entorno ni en `.env`
- **THEN** el command no realiza ninguna petición HTTP y termina con código 0

#### Scenario: API key configurada con servidor inalcanzable
- **WHEN** `NIERIKA_API_KEY` está definida y `NIERIKA_API_BASE_URL` no responde
- **THEN** el command falla con error no-cero y mensaje que no incluye el valor de la key

### Requirement: Espejo almacena hechos crudos sin datos personales
La tabla espejo SHALL persistir exclusivamente `id` (UUID de Nierika, PK), `serial_number`, `issued_at`, `expiration_date`, `max_expiration_date`, `revoked_at` y `synced_at`. Los campos del payload de Nierika sin significado en este dominio (p.ej. `ScanKind`) NO se persistirán. NO almacenará nombre, matrícula, fotografía ni datos del titular. El `id` es la PK asignada por Nierika (no se genera localmente).

#### Scenario: Credencial emitida queda reflejada
- **WHEN** el command descarga una credencial con sus campos mínimos
- **THEN** existe una fila local con exactamente esos campos más `synced_at`, sin campos del titular

#### Scenario: Fila del catálogo sin techo de vigencia
- **WHEN** el catálogo trae una credencial sin `MaxExpirationDate`
- **THEN** el command la salta con un warning (id/serial) y no la persiste; el resto de la descarga continúa con exit code 0

### Requirement: Estado derivado por precedencia
El estado de una credencial (`Active`/`Revoked`/`Expired`) SHALL calcularse en Django con precedencia `Revoked > Expired > Active` evaluada contra la hora UTC actual, con el mismo criterio que el backend Nierika (`DeriveStatus`). El estado NO se persiste en la base de datos.

#### Scenario: Revocada tiene precedencia sobre expirada
- **WHEN** una credencial tiene `revoked_at` no nulo y `expiration_date` ya pasada
- **THEN** su estado derivado es `Revoked`

#### Scenario: Expiración por transcurso del tiempo
- **WHEN** una credencial sin `revoked_at` tiene `expiration_date` ya pasada
- **THEN** su estado derivado es `Expired` aunque nadie la haya modificado desde su alta
