# Tasks — add-nierika-integration

## 1. App `integrations` y modelos

- [x] 1.1 Crear `src/integrations/` (`apps.py`, `models/`, `migrations/`, `tests.py`) y registrarla en `INSTALLED_APPS` (settings) y en `module-name` de `pyproject.toml`.
- [x] 1.2 Crear modelo `Credential` (PK `id` UUID sin default — proviene de Nierika; `serial_number` indexado; `issued_at`, `expiration_date`, `max_expiration_date`, `revoked_at` nullable, `synced_at`) con propiedad `status` derivada (precedencia `Revoked > Expired > Active` contra `timezone.now()`).
- [x] 1.3 Crear modelo `StudentCredential` (`student` FK → `school.Student`, `credential` FK → `integrations.Credential` con `unique=True`, `linked_at`, `unlinked_at` nullable) con constraint/garantía de máximo una relación activa (`unlinked_at IS NULL`) por estudiante.
- [x] 1.4 Crear modelo `DesktopApiKey` (`name`, `prefix` indexado, `hash`, `created_at`, `revoked_at` nullable) + migración inicial de la app. **Given** las migraciones aplicadas, **When** se inspecciona el schema, **Then** existen las tres tablas con sus índices y constraints.
- [x] 1.5 Agregar tests de modelo: estado derivado (revocada > expirada > activa), unicidad de credencial en la relación, constraint de una relación activa por estudiante.

## 2. Configuración de entorno

- [x] 2.1 Agregar `NIERIKA_API_BASE_URL` y `NIERIKA_API_KEY` (ambas con default vacío) vía `environ.Env` en `src/config/settings.py`. Documentarlas en `.env.example`.
- [x] 2.2 Tests/settings: **Given** ninguna variable definida, **When** se importan settings, **Then** ambas son cadenas vacías y `manage.py check` pasa.

## 3. Cliente de sincronización y management command

- [x] 3.1 Crear `integrations/nierika.py`: cliente HTTP (stdlib `urllib`, sin dependencias nuevas) con `GET /api/integrations/me/credentials` paginado por cursor `(createdAt, Id)` + `limit` (default 500 configurable), header `X-API-Key`, timeout y manejo de 401/5xx con error que nunca loggee el valor de la key. Extraer a función pura el mapeo del JSON de página a dicts de campos del modelo.
- [x] 3.2 Crear command `sync_nierika_credentials`: **Given** `NIERIKA_API_KEY` vacía, **When** corre el command, **Then** no hace peticiones HTTP y termina con código 0 y mensaje informativo. **Given** key configurada, **When** corre, **Then** itera todas las páginas y upserta por `id` fijando `synced_at`; filas del catálogo sin `MaxExpirationDate` se saltan con warning (sin abortar, exit 0).
- [x] 3.3 Tests del command con `responses`/mock de `urllib` (o inyección del cliente): paginación completa, upsert idempotente en re-ejecución, actualización de fila desactualizada, no-op sin key, fallo con key y servidor caído (exit no-cero, sin filtrar la key en el mensaje).

## 4. API keys del escritorio y management commands

- [x] 4.1 Crear `integrations/keys.py`: generación con `secrets.token_*` (~256 bits, base62, prefijo `dsk_`), extracción de `prefix` (~10 chars), hash SHA-256 hex.
- [x] 4.2 Crear command `create_desktop_api_key --name <etiqueta>` (imprime key completa una sola vez + prefijo + advertencia show-once) y `revoke_desktop_api_key --prefix <prefijo>` (falla si ya revocada o prefijo inexistente).
- [x] 4.3 Tests: formato de key, show-once (no queda valor en claro en DB), revocación y revocación duplicada.

## 5. Auth y endpoints de escritorio (`src/api`)

- [x] 5.1 Crear `DesktopApiKeyAuth(APIKeyHeader)` en `src/api/auth.py`: header `X-API-Key`, lookup por `prefix`, `hmac.compare_digest` del hash, verificación de no revocada; fallo → 401 genérico idéntico para ausente/inexistente/revocada.
- [x] 5.2 Crear `src/api/desktop.py`: router `Router(auth=DesktopApiKeyAuth())` con `GET /students` (id, nombres, email, grupos, `has_photo`, `photo_url`) y `GET /students/{id}/photo` (bytes de `Student.photo`, `image/jpeg`; 404 sin foto o sin estudiante). Montar el router en `src/api/api.py` sin tocar la operación existente.
- [x] 5.3 Tests de endpoints (patrón `src/api/tests.py`): 401 genérico en los tres casos de auth inválida; padrón completo de estudiantes; foto 200/404; suite existente de asistencia sigue verde.

## 6. Endpoint de eventos push

- [x] 6.1 Crear schemas ninja del evento discriminado (`operation` literal: `issued` | `revoked` | `validity_extended` + payload por operación + `occurred_at`) en `src/api/schemas.py` (o módulo propio) y handler `POST /credential-events` en el router de escritorio.
- [x] 6.2 Implementar aplicación del evento `issued` en transacción: upsert de `Credential` por `id`; cierre de relación activa previa del estudiante; creación de `StudentCredential`; idempotencia ante reenvío (mismo resultado). 422 si `student_id` no existe.
- [x] 6.3 Implementar `revoked` (fija `revoked_at`, cierra relación activa) y `validity_extended` (actualiza `expiration_date` dentro del techo inmutable `max_expiration_date`); 404 si la credencial no existe en el espejo; 422 si `operation` no es de las tres soportadas o si la vigencia pretendida excede el techo (`ExpirationBeyondMax`, también en `issued`).
- [x] 6.4 Tests end-to-end del endpoint: emisión crea credencial + relación; reemisión cierra la anterior; reenvío idempotente; revocación cierra relación; extended actualiza; 404 de evento huérfano; 422 de operation inválida y de estudiante inexistente.

## 7. Verificación final

- [x] 7.1 Correr `uv run manage.py check` y la suite completa `uv run manage.py test`; corregir regresiones.
- [x] 7.2 Verificar el contrato contra la spec de Nierika (`integrations-v1`): campos del payload, cursor, header `X-API-Key`; documentar la entrada de cron sugerida para `sync_nierika_credentials` en el design o README de la app.
- [x] 7.3 Recorrido manual: generar key con el command, llamar `/api/desktop/students` y `/credential-events` con curl, correr sync contra mocks y confirmar no-op sin `NIERIKA_API_KEY`.

## 8. Separación de dominio (amend post-implementación)

- [x] 8.1 Extraer app core `src/credentials/` (`Credential`, `StudentCredential`, `events.py`, tests de dominio) y rescopear `src/integrations/` como dominio de integraciones externas (Nierika: `nierika.py` + `sync_nierika_credentials`; escritorio: `DesktopApiKey` + `keys.py` + commands), con migraciones frescas por app (tablas `credentials_*` / `integrations_desktopapikey`).
- [x] 8.2 Reconectar: `INSTALLED_APPS` + `module-name` de `pyproject.toml`, imports en `src/api` (`desktop.py` → `credentials.events`, `tests.py`), command `sync_nierika_credentials` (→ `credentials.models`); READMEs por app; suite completa en verde.

## 9. Endpoints de escritorio asíncronos (amend post-implementación)

- [x] 9.1 Convertir las operaciones del router de escritorio (`/students`, `/students/{id}/photo`, `/credential-events`) a `async def`: iteración async del padrón (prefetch cacheado), `afirst` + `sync_to_async` para la lectura de foto, eventos aplicados vía `sync_to_async`. `credentials/events.py` sin cambios (núcleo transaccional sync; Django 6.1 no soporta atomic async). Auth sync intacta (ninja la corre en threadpool).
- [x] 9.2 Verificación: `check` limpio y suite completa en verde (160 tests, comportamiento idéntico).

## 10. Reestructuración interna de `api` (amend post-implementación)

- [x] 10.1 Mover endpoints a `src/api/endpoints/` (`desktop.py` → `credentials.py`; operación de asistencia extraída de `api.py` → `attendance.py` como router montado en `''` que hereda `TeacherSessionAuth`) y schemas a `src/api/schemas/` en dos archivos temáticos (`attendance.py`, `credentials.py`) con re-exports en el `__init__`; `api.py` queda solo con el wiring de `NinjaAPI` + mounts.
- [x] 10.2 Verificación: URLs sin cambios (`api:update_session_records`, `api:*`), `check` limpio, suite completa en verde (160 tests).
