# credentials

Dominio core de gestión de credenciales. No sabe nada de Nierika ni de
ningún otro emisor: un emisor futuro escribiría en este mismo dominio
(vía `events.py` o su propio sync) sin tocar código de integración.

## Modelos

- `Credential` — espejo de hechos crudos (`id` UUID asignado por el emisor
  como PK, `serial_number`, fechas de emisión/vigencia, `revoked_at`,
  `scan_kind`, `synced_at`). Sin datos personales del titular. El estado
  (`Active`/`Expired`/`Revoked`) es una propiedad derivada con precedencia
  `Revoked > Expired > Active` contra la hora UTC; no se persiste.
- `StudentCredential` — vínculo estudiante↔credencial con historial
  (`linked_at`/`unlinked_at`). Garantía: máximo una relación activa
  (`unlinked_at IS NULL`) por estudiante; una credencial pertenece a un solo
  estudiante.

## Aplicación de eventos (`events.py`)

Lógica transaccional de mutación del espejo, consumida por el endpoint push
`POST /api/desktop/credential-events` (router en la app `api`):

- `apply_issued_event` — upsert de `Credential` + vínculo con el estudiante
  (cierra la relación activa previa; idempotente ante reenvío; 422 si el
  estudiante no existe).
- `apply_revoked_event` — fija `revoked_at` y cierra la relación activa
  (404 si la credencial no existe).
- `apply_validity_extended_event` — actualiza vigencias (404 si no existe).
