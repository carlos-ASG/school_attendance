# Authentication & CSRF

## Where to set auth

Three levels, more specific wins:

```python
api = NinjaAPI(auth=GlobalAuth())            # 1. global
router = Router(auth=BasicAuth())            # 2. router (overrides global)
@api.get("/x", auth=SessionAuth())           # 3. operation (overrides both)
def x(request): ...
```

`auth=None` on an operation/router disables inherited auth (useful for
login/token endpoints under global auth).

Every authenticator's return value is stored in `request.auth`; falsy return →
401. First argument is always the Django `request`.

## Built-in authenticators (ninja.security)

| Class / callable             | Source of credentials        | Notes                                   |
| ---------------------------- | ---------------------------- | --------------------------------------- |
| `django_auth` (callable)     | Django session cookie        | Any logged-in user; CSRF auto-enabled   |
| `django_auth_superuser`      | Django session               | Superusers only                         |
| `SessionAuth()`              | Django session               | Logged-in users                         |
| `SessionAuthSuperUser()`     | Django session               | `is_superuser`                          |
| `SessionAuthIsStaff()`       | Django session               | Superuser **or** staff                  |
| `HttpBearer`                 | `Authorization: Bearer <t>`  | Subclass, implement `authenticate`      |
| `HttpBasicAuth`              | `Authorization: Basic`       | `authenticate(request, username, password)` |
| `APIKeyQuery`                | `?key=...` (`param_name`)    | Subclass, implement `authenticate`      |
| `APIKeyHeader`               | header (`param_name`)        | e.g. `X-API-Key`                        |
| `APIKeyCookie`               | cookie                       | CSRF auto-enabled                       |
| plain function               | anything                     | `def my_auth(request): ...`             |

```python
from ninja.security import HttpBearer, APIKeyHeader

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        if token == "supersecret":
            return token           # → request.auth

class ApiKey(APIKeyHeader):
    param_name = "X-API-Key"
    def authenticate(self, request, key):
        try:
            return Client.objects.get(key=key)
        except Client.DoesNotExist:
            pass

@api.get("/bearer", auth=AuthBearer())
def bearer(request):
    return {"token": request.auth}
```

Multiple authenticators (`auth=[A(), B()]`) are tried in order; first success
wins, else 401. Custom async callables are supported for async views; the
built-in classes are not async-compatible.

OpenAPI docs show an **Authorize** button for the configured auth class.

## CSRF (reference/crf behavior)

- **OFF by default for every operation.**
- Auto-ENABLED when the effective auth is cookie-based (`django_auth`,
  `SessionAuth`, `APIKeyCookie`).
- For session-cookie APIs (frontend with cookies), either rely on the
  auto-enable with `django_auth`, or pass `NinjaAPI(csrf=ON)` and let the
  frontend send Django's CSRF token per the Django AJAX docs.
- Enabling a token endpoint for the frontend (order matters — route decorator
  on top):

```python
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

@api.post("/csrf", auth=None)   # disable cookie auth here or it raises
@ensure_csrf_cookie
@csrf_exempt
def get_csrf_token(request):
    return HttpResponse()
```

- CORS is separate; use django-cors-headers if frontend and API are on
  different origins.

## Custom auth exceptions

```python
class InvalidToken(Exception):
    pass

@api.exception_handler(InvalidToken)
def on_invalid_token(request, exc):
    return api.create_response(request, {"detail": "Invalid token"}, status=401)

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        if token == "supersecret":
            return token
        raise InvalidToken
```
