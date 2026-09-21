## Why

El ecosistema Nierika gestiona las credenciales digitales de los estudiantes (emisión, revocación, vigencia) pero el sistema de control escolar en Django no tiene forma de conocer ese catálogo ni de vincularlo con sus estudiantes. El backend de Nierika está implementando la integración `add-issuer-api-keys` (descarga completa del catálogo vía API key) y delega el flujo de mutaciones a notificaciones push desde la app de escritorio hacia Django, autenticadas con una API key emitida por el propio Django. Sin este change, Django queda fuera de ese flujo y no puede asociar estudiantes con sus credenciales.

## What Changes

- Nueva app Django `integrations`: espejo local del catálogo de credenciales de Nierika (`Credential`), relación estudiante-credencial (`StudentCredential`) y API keys emitidas por Django para las estaciones de escritorio (`DesktopApiKey`).
- Cliente HTTP + management command `sync_nierika_credentials` que descarga el catálogo completo del emisor desde `GET {NIERIKA_API_BASE_URL}/api/integrations/me/credentials` (paginado por cursor, upsert idempotente por id). **No-op si `NIERIKA_API_KEY` no está configurada.**
- Polling de reconciliación por cron del sistema que ejecuta el command de forma ocasional (reparación de pushes perdidos), solo cuando la API key está configurada.
- Nueva autenticación API key para el escritorio: header `X-API-Key` con key emitida por Django (hash SHA-256 + prefijo, show-once, revocable), gestionada vía management commands.
- Nuevos endpoints de API (django-ninja, protegidos por la key del escritorio):
  - `GET /api/desktop/students`: información completa de estudiantes (incluye URL de foto).
  - `GET /api/desktop/students/{id}/photo`: bytes de la fotografía, protegidos por la misma API key.
  - `POST /api/desktop/credential-events`: notificación push discriminada por operación (`issued`, `revoked`, `validity_extended`) con `occurred_at`, idempotente y reenviable (desktop offline). El evento `issued` crea la credencial y la relación estudiante-credencial en un solo paso.
- Estado derivado de la credencial (`Active`/`Revoked`/`Expired`, precedencia Revoked > Expired > Active) calculado en Django sobre los hechos crudos, con el mismo criterio que Nierika.

## Capabilities

### New Capabilities

- `credential-mirror`: espejo local del catálogo de credenciales del emisor (descarga completa paginada, upsert idempotente, reconciliación periódica condicionada a API key configurada, estado derivado por precedencia).
- `desktop-api-auth`: ciclo de vida de API keys emitidas por Django para estaciones de escritorio (generación show-once vía management command, revocación, autenticación por header `X-API-Key` con hash + prefijo).
- `desktop-integration-api`: endpoints autenticados para la app de escritorio: descarga del padrón de estudiantes (con foto protegida) y notificaciones push de mutaciones de credenciales (issued/revoked/validity_extended) idempotentes.

### Modified Capabilities

- `environment-configuration`: nuevas variables de entorno `NIERIKA_API_BASE_URL` y `NIERIKA_API_KEY` (opcional; sin ella la sincronización no corre).

## Impact

- **Nueva app**: `src/integrations/` (modelos, cliente de sync, management commands, tests); se agrega a `INSTALLED_APPS` y a `module-name` en `pyproject.toml`.
- **App `api`**: nuevo router `/api/desktop/*` con auth `DesktopApiKeyAuth` (coexiste con el `TeacherSessionAuth` existente).
- **Configuración**: settings nuevos en `src/config/settings.py` (patrón `environ` existente).
- **Despliegue**: entrada de cron documentada para `uv run manage.py sync_nierika_credentials`; generación de keys del escritorio con management commands.
- **Dependencias externas**: endpoint `GET /api/integrations/me/credentials` del backend Nierika (change `add-issuer-api-keys`, contrato fijado en su spec; aún en implementación allá — el cliente se construye contra el contrato con mocks).
- **Sin cambios rompientes**: no se modifica ningún modelo, vista o endpoint existente.

## No objetivos

- No se implementa sincronización incremental ni bitácora de eventos: el plan de Nierika fue re-dirigido; las mutaciones llegan por push desde el escritorio y la descarga completa es solo reconciliación.
- No se incluyen datos personales del titular en el payload de sincronización (contrato de Nierika, tampoco aplica).
- No se implementa autenticación de operador (usuario/contraseña) para el escritorio: solo API key por estación.
- No se implementan webhooks desde Nierika hacia Django, rotación automática de keys ni rate limiting específico de los endpoints de escritorio.
- No se modifican los flujos de asistencia ni el panel de profesores; la relación estudiante-credencial es solo almacenamiento y consulta futura.
