# Spec Delta — environment-configuration

## ADDED Requirements

### Requirement: Variables de integración Nierika
Las variables `NIERIKA_API_BASE_URL` (URL base del backend Nierika, sin `/` final) y `NIERIKA_API_KEY` (API key del emisor, formato `nkb_...`) SHALL leerse vía `django-environ` en settings, con ambas vacías por default. `.env.example` SHALL documentarlas con placeholders. La ausencia de `NIERIKA_API_KEY` SHALL desactivar la sincronización de credenciales (no-op) sin afectar el resto de la aplicación.

#### Scenario: Sin configuración la app funciona igual
- **WHEN** el proyecto corre con ninguna de las dos variables definidas
- **THEN** Django arranca normalmente, los endpoints de escritorio y la API de profesores operan, y el command de sync es no-op

#### Scenario: Configuración desde .env
- **WHEN** `.env` define `NIERIKA_API_BASE_URL=https://nierika.example.com` y `NIERIKA_API_KEY=nkb_...`
- **THEN** el command de sincronización usa esos valores para autenticarse contra el backend
