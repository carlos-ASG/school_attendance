# Design — add-nierika-integration

## Context

El ecosistema Nierika (backend C# en `Nierika_backend`, escritorio Electron en `escorpio_escuelas`) gestiona el ciclo de vida de credenciales digitales de estudiantes. El backend está implementando el change `add-issuer-api-keys` cuya dirección final es:

- Un endpoint machine-to-machine `GET /api/integrations/me/credentials` (header `X-API-Key` con key `nkb_...` por emisor) que devuelve la **descarga completa** del catálogo paginada por cursor `(CreatedAt, Id)`. Payload mínimo por credencial: `Id`, `SerialNumber`, estado derivado, `IssuedAt`, `ExpirationDate`, `MaxExpirationDate`, `RevokedAt?`, `ScanKind`. Sin datos personales del titular.
- **Sin** bitácora ni sincronización incremental: las mutaciones posteriores (emisión, revocación, reemisión, extensión) las notifica la app de escritorio **push directamente a Django**, autenticadas con una API key **emitida por el propio Django**. Ese canal es externo al backend Nierika.

El sistema de control escolar (este repo, Django 6 + django-ninja + HTMX + SQLite, gestionado con `uv`) posee el padrón de estudiantes (`school.Student`: nombres, email, foto, grupos) y la asistencia, pero no conoce las credenciales. La app de escritorio hoy sincroniza alumnos desde una BD escolar por ETL TCP directo; con esta integración consumirá el padrón desde Django vía API REST.

Restricciones verificadas en el código:

- `src/api/` ya existe con django-ninja (`NinjaAPI` con `TeacherSessionAuth` basado en sesión/CSRF). Los endpoints de escritorio necesitan un esquema de auth distinto (API key), coexistente.
- No hay Celery, colas ni scheduler en el proyecto; el patrón de fondo existente son management commands (`seed_dev_data`, etc.).
- Settings ya usan `django-environ` con defaults de desarrollo; la DB es SQLite (`db.sqlite3`).
- `Student` usa `UUIDv7Model` (PK UUIDv7) — el id de estudiante es estable y apto para referenciar desde el escritorio.

## Goals / Non-Goals

**Goals:**

- Espejo local del catálogo de credenciales del emisor, mantenido fresco por (a) push del escritorio en cada mutación y (b) reconciliación periódica por descarga completa.
- Relación estudiante↔credencial persistida en Django (una credencial → un estudiante; un estudiante → máximo una relación activa, con historial).
- Autenticación machine-to-machine del escritorio con API key emitida por Django (hash + prefijo, show-once, revocable).
- Endpoints de solo lectura del padrón de estudiantes y recepción de eventos, idempotentes y tolerantes a reenvío (el escritorio opera offline y encola eventos).
- La sincronización con Nierika corre solo si la API key del emisor está configurada; sin ella, no-op silencioso.

**Non-Goals:**

- Sincronización incremental o bitácora de eventos (el backend Nierika descartó ambas).
- Autenticación de operador humano contra Django (usuario/contraseña); el escritorio usa API key por estación.
- Rotación automática de keys, expiración, `LastUsedAt`, scopes, rate limiting específico.
- UI en Django para gestionar keys ni credenciales (gestión vía admin/management commands y consumo futuro por otros módulos).
- Webhooks, SignalR ni notificaciones push desde Django hacia terceros.

## Decisions

### D1. App dedicada `integrations`

Todo lo nuevo vive en `src/integrations/`: modelos (`Credential`, `StudentCredential`, `DesktopApiKey`), cliente HTTP de sync, management commands y tests. Los endpoints de escritorio se montan como router adicional dentro de la app `api` existente (que ya concentra la API ninja), importando modelos de `integrations`.

Alternativa descartada: meter los modelos en `school`. Mezclaría el dominio académico con integración externa y ensuciaría las migraciones del core.

### D2. Espejo de credenciales: hechos crudos + estado derivado

`Credential` persiste solo hechos: `id` (UUID de Nierika, PK, no generado), `serial_number`, `issued_at`, `expiration_date`, `max_expiration_date`, `revoked_at`, `scan_kind`, `synced_at`. El estado (`Active`/`Revoked`/`Expired`) es una **propiedad calculada** con precedencia `Revoked > Expired > Active` contra UTC — el mismo criterio de `DeriveStatus` en Nierika. No se persiste el estado: evita datos obsoletos (una credencial expira con el paso del tiempo aunque nadie la toque).

Upsert idempotente por `id` tanto en la descarga completa como en el evento `issued` (mismo criterio que el cliente Django previsto por el design de Nierika).

### D3. Push como fuente primaria; descarga completa como reconciliación

El escritorio notifica cada mutación (`issued`, `revoked`, `validity_extended`) con `occurred_at` del escritorio. Django aplica los eventos en el orden recibido (confía en el orden del cliente; el desktop encola en orden). La descarga completa se re-ejecuta por cron de forma ocasional (p.ej. cada 30–60 min) como reparación: upsert idempotente sobre todo el catálogo corrige cualquier push perdido.

El command `sync_nierika_credentials` lee `NIERIKA_API_BASE_URL` y `NIERIKA_API_KEY` de settings (`environ`); si la key falta, sale con log informativo y código 0. La frecuencia exacta queda en el crontab del despliegue, no en código.

Alternativa descartada: polling frecuente como fuente primaria. Sin endpoint incremental, implicaría descargar el catálogo completo constantemente, y contradice la dirección del change de Nierika.

### D4. Un solo endpoint de eventos, discriminado por operación

`POST /api/desktop/credential-events` recibe `{operation, occurred_at, ...}` con payload por operación:

- `issued`: `{credential: {id, serial_number, issued_at, expiration_date, max_expiration_date, scan_kind}, student_id}` → upsert de `Credential` + cierre de la relación activa previa del estudiante (reemisión) + creación de `StudentCredential`. Idempotente: repetir el mismo `issued` no duplica.
- `revoked`: `{credential_id, revoked_at}` → fija `revoked_at` y cierra la relación activa.
- `validity_extended`: `{credential_id, expiration_date, max_expiration_date}` → actualiza vigencias.

`revoked`/`validity_extended` sobre credencial desconocida → **404** (decisión explícita): el push de `issued` es la fuente de alta; si se perdió, la reconciliación por cron repara el espejo y el escritorio puede reintentar.

Alternativa descartada: endpoints discretos por operación. Más superficie de API y obliga al escritorio a manejar varias rutas; el evento único encaja con una cola de eventos offline reenviable en orden.

### D5. API key del escritorio: hash + prefijo, show-once, gestión por management commands

`DesktopApiKey`: `name` (etiqueta de estación), `prefix` (primeros ~10 chars, index), `hash` (SHA-256 hex de la key completa), `created_at`, `revoked_at`. Generación con `secrets` (~256 bits, base62, formato `dsk_<43+>`); lookup por prefijo + comparación timing-safe (`hmac.compare_digest`) + `revoked_at is null`. Fallo → 401 genérico indistinguible (no facilitar enumeración).

Show-once vía management commands: `create_desktop_api_key --name "estacion-x"` imprime la key completa una sola vez; `revoke_desktop_api_key --prefix dsk_7f3a1b`. No se construye UI: el volumen de estaciones es bajo y el patrón show-once es natural en CLI.

Alternativa descartada: admin de Django para generar. El show-once en admin exige pantalla dedicada de confirmación; el management command es más simple y consistente con el resto del proyecto (sin UI para operaciones de integración).

### D6. Auth ninja por API key, coexistente con la sesión de profesor

Nuevo `DesktopApiKeyAuth(APIKeyHeader)` (header `X-API-Key`) aplicado a un `Router` de escritorio montado en el `NinjaAPI` existente. El `TeacherSessionAuth` actual sigue intacto en su operación. La foto se sirve por endpoint protegido (`GET /api/desktop/students/{id}/photo` → bytes del `ImageField`), no por URL pública de media: coherente con la privacidad del resto de la API.

### D7. Foto de estudiante en el padrón

`GET /api/desktop/students` devuelve por estudiante: `id`, `first_name`, `paternal_surname`, `maternal_surname`, `email`, grupos (nombres), `has_photo` y `photo_url` (ruta del endpoint protegido, relativa). El escritorio descarga las fotos que le interesen con la misma key y las gestiona localmente (su autoridad sobre fotos sigue siendo la estación, como en su esquema híbrido actual).

## Risks / Trade-offs

- [Push perdido deja el espejo desactualizado hasta el próximo cron] → Mitigación: cron de reconciliación frecuente; descarga completa idempotente como reparación (mecanismo explícito del design de Nierika). Aceptable por consistencia eventual.
- [Evento `revoked`/`validity_extended` llega antes que su `issued` (reenvío desordenado)] → Mitigación: 404 y el escritorio reintenta; la cola del desktop se reenvía en orden, así que es un caso de borde de primera entrega. Documentado en el contrato del endpoint.
- [Reloj del escritorio desviado corrompe `occurred_at`] → Mitigación: Django registra también `received_at` server-side; el orden de aplicación usa el orden de recepción, `occurred_at` queda como dato informativo.
- [Fuga de la API key del escritorio expone el padrón de estudiantes (PII)] → Mitigación: hash + prefijo (nunca en claro en DB), show-once, revocación por command, 401 genérico. La key protege el endpoint más sensible (fotos + padrón); rotación manual documentada.
- [Key de Nierika (`nkb_...`) distinta de la key del escritorio (`dsk_...`)] → Aceptado: son dominios de confianza distintos (emisor↔Django vs estación↔Django); los formatos diferencian el origen.
- [Endpoint de Nierika aún no implementado en el backend] → El cliente Django se construye contra el contrato fijado en su spec (`integrations-v1`) y se prueba con mocks; la integración end-to-end espera al deploy de ese change.
- [Crecimiento de `StudentCredential` (historial)] → Filas pequeñas (2 FK + timestamps); volumen escolar es manejable. Sin purga en esta iteración.

## Migration Plan

1. Crear la app `integrations` con sus modelos y migración (tablas nuevas; sin tocar datos existentes).
2. `uv run manage.py migrate`.
3. Configurar `NIERIKA_API_BASE_URL` y `NIERIKA_API_KEY` (del portal del emisor en Nierika) en el entorno.
4. Generar key(s) del escritorio: `uv run manage.py create_desktop_api_key --name "estacion-x"` y configurarla en la app de escritorio.
5. Primera descarga completa: `uv run manage.py sync_nierika_credentials`.
6. Instalar entrada de cron para la reconciliación periódica.
7. Rollback: revertir código + migraciones (`migrate integrations zero`); las tablas quedan vacías de efecto; las keys revocadas invalidan al escritorio de inmediato.

## Open Questions

Ninguna bloqueante. A resolver en implementación:

- Nombre final de las variables de entorno (`NIERIKA_API_BASE_URL`/`NIERIKA_API_KEY` vs. prefijo `CREDENTIALS_...`), siguiendo el estilo del `.env` actual.
- Valor exacto del `limit` por página al consumir el endpoint de Nierika (default razonable: 500, ajustable por settings).
- Valores concretos de `scan_kind` que Nierika emite (se almacena como texto libre hasta conocer el catálogo).
