# integrations

Integraciones externas y estaciones de escritorio: sincronización con el
emisor Nierika y API keys para las estaciones. Los modelos del dominio
(espejo de credenciales y vínculo estudiante↔credencial) viven en la app
core `credentials` (ver `src/credentials/README.md`).

## Contrato con Nierika (`integrations-v1`, change `add-issuer-api-keys`)

El cliente (`nierika.py`) está construido contra el contrato fijado en la
espec de Nierika:

- Endpoint: `GET {NIERIKA_API_BASE_URL}/api/integrations/me/credentials`
- Autenticación: header `X-API-Key: {NIERIKA_API_KEY}` (key del emisor,
  formato `nkb_...`)
- Paginación por cursor compuesto `(createdAt, Id)`: el cliente manda
  `?limit={limit}&cursor={cursor}` y sigue el cursor opaco devuelto por el
  servidor hasta `hasMore=false` (default `limit=500`)
- Campos por credencial: `Id`, `SerialNumber`, `IssuedAt`, `ExpirationDate`,
  `MaxExpirationDate`, `RevokedAt?`, `ScanKind` (PascalCase, fechas ISO 8601)

> Pendiente: verificación end-to-end del contrato cuando el backend Nierika
> despliegue el change `add-issuer-api-keys`; hasta entonces el cliente se
> valida con mocks.

## Sincronización (reconciliación por descarga completa)

```bash
uv run manage.py sync_nierika_credentials
```

- No-op (exit 0, sin llamadas HTTP) si `NIERIKA_API_KEY` no está configurada.
- Upsert idempotente por `id` en `credentials.Credential` fijando `synced_at`;
  corrige pushes perdidos.

Entrada de cron sugerida (cada 30–60 min, según despliegue):

```cron
17 * * * * cd /ruta/al/proyecto && uv run manage.py sync_nierika_credentials >> var/log/nierika-sync.log 2>&1
```

## Variables de entorno (`.env`)

- `NIERIKA_API_BASE_URL` — URL base del backend Nierika, sin `/` final
- `NIERIKA_API_KEY` — key del emisor (`nkb_...`); vacía = sync desactivado

## API keys del escritorio

`DesktopApiKey` (hash SHA-256 + prefijo de 10 chars; el valor completo nunca
se persiste) alimenta la auth de los endpoints `/api/desktop/*`.

```bash
uv run manage.py create_desktop_api_key --name "estacion-direccion"   # show-once
uv run manage.py revoke_desktop_api_key --prefix dsk_7f3a1b
```

Endpoints de escritorio (django-ninja, header `X-API-Key: dsk_...`):

- `GET /api/desktop/students` — padrón completo (grupos, `has_photo`,
  `photo_url`)
- `GET /api/desktop/students/{id}/photo` — bytes JPEG de la fotografía
- `POST /api/desktop/credential-events` — push de mutaciones hacia el
  dominio `credentials`: `issued` (alta + vínculo), `revoked`,
  `validity_extended`; idempotente y en orden de recepción. Cualquier fallo
  de autenticación produce un 401 genérico idéntico.

Las tres operaciones son vistas `async def` (beneficio de concurrencia bajo
servidor ASGI como uvicorn/daphne; bajo `runserver`/WSGI funcionan igual).
La lógica transaccional de eventos vive síncrona en `credentials/services.py`
y se invoca vía `sync_to_async` (Django 6.1 no soporta atomic async).
