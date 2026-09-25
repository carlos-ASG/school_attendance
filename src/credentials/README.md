# credentials

Dominio core de gestión de credenciales. No sabe nada de Nierika ni de
ningún otro emisor: un emisor futuro escribiría en este mismo dominio
(vía `services.py` o su propio sync) sin tocar código de integración.

## Modelos

- `Credential` — espejo de hechos crudos (`id` UUID asignado por el emisor
  como PK, `serial_number`, fechas de emisión/vigencia, `revoked_at`,
  `synced_at`). Sin datos personales del titular. El estado
  (`Active`/`Expired`/`Revoked`) es una propiedad derivada con precedencia
  `Revoked > Expired > Active` contra la hora UTC; no se persiste.
- `StudentCredential` — vínculo estudiante↔credencial con historial
  (`linked_at`/`unlinked_at`). Garantía: máximo una relación activa
  (`unlinked_at IS NULL`) por estudiante; una credencial pertenece a un solo
  estudiante.

## Aplicación de eventos (`services.py`)

Lógica transaccional de mutación del espejo, consumida por el endpoint push
`POST /api/desktop/credential-events` (router en la app `api`). Los errores
de dominio (`StudentNotFoundError`, `CredentialNotFoundError`) son traducidos por el
endpoint a 422/404:

- `credential_issue` — upsert de `Credential` + vínculo con el estudiante
  (cierra la relación activa previa; idempotente ante reenvío;
  `StudentNotFoundError` si el estudiante no existe; `MaxExpirationRequiredError` si
  falta el techo `max_expiration_date`, obligatorio en el alta;
  `ExpirationBeyondMaxError` si la vigencia excede su `max_expiration_date`).
- `credential_revoke` — fija `revoked_at` y cierra la relación activa
  (`CredentialNotFoundError` si no existe).
- `credential_extend_validity` — actualiza `expiration_date` dentro del
  techo `max_expiration_date` (inmutable tras el alta; `ExpirationBeyondMaxError`
  si se excede) (`CredentialNotFoundError` si no existe).
