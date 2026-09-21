# Spec Delta — desktop-api-auth

## ADDED Requirements

### Requirement: API key del escritorio con almacenamiento hash + prefijo
El sistema SHALL proveer el modelo `DesktopApiKey` con `name` (etiqueta de estación), `prefix` (primeros caracteres de la key, indexado), `hash` (SHA-256 hex de la key completa), `created_at` y `revoked_at` (nullable). El valor completo de la key SHALL existir solo en el momento de la generación (show-once) y nunca persistirse en claro ni ser recuperable después.

#### Scenario: Key generada no es recuperable
- **WHEN** se consulta la base de datos tras generar una key
- **THEN** solo existen `prefix` y `hash`; no hay columna ni registro con el valor completo

#### Scenario: Formato de key generada
- **WHEN** se genera una key con el management command
- **THEN** el valor impreso tiene formato `dsk_<43+ caracteres base62>` (~256 bits de entropía)

### Requirement: Generación y revocación por management commands
El sistema SHALL proveer `create_desktop_api_key --name <etiqueta>` que genere la key, persista hash + prefijo e imprima el valor completo una sola vez en stdout. SHALL proveer `revoke_desktop_api_key --prefix <prefijo>` que fije `revoked_at`. Revocar una key ya revocada SHALL fallar con mensaje claro.

#### Scenario: Generación muestra la key una sola vez
- **WHEN** el administrador ejecuta `create_desktop_api_key --name "estacion-direccion"`
- **THEN** el comando imprime la key completa junto a su prefijo y mensaje de que no se volverá a mostrar

#### Scenario: Revocación invalida la key
- **WHEN** se ejecuta `revoke_desktop_api_key` con el prefijo de una key activa
- **THEN** la key queda con `revoked_at` fijado y deja de autenticar

#### Scenario: Revocación duplicada falla
- **WHEN** se revoca una key ya revocada
- **THEN** el comando termina con error y mensaje indicando que ya estaba revocada

### Requirement: Autenticación por header X-API-Key con 401 genérico
Los endpoints del escritorio SHALL autenticarse con el header `X-API-Key`: lookup por `prefix`, comparación timing-safe del hash con `hmac.compare_digest`, y verificación de que la key no está revocada. Key inexistente, revocada o header ausente SHALL producir el mismo 401 genérico, sin distinguir el motivo (anti-enumeración).

#### Scenario: Key válida autentica
- **WHEN** un request presenta una key activa y correcta
- **THEN** el endpoint procesa la petición

#### Scenario: Key revocada e inexistente son indistinguibles
- **WHEN** un request presenta una key revocada, una key inventada o ningún header
- **THEN** en los tres casos la respuesta es 401 con el mismo cuerpo
