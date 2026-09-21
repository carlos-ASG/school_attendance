import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from datetime import datetime
from typing import Any
from uuid import UUID

DEFAULT_PAGE_LIMIT = 500
REQUEST_TIMEOUT_SECONDS = 30
CREDENTIALS_PATH = '/api/integrations/me/credentials'


class NierikaClientError(Exception):
    """No se pudo contactar el API de Nierika (los mensajes nunca incluyen la key)."""


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def parse_credential_item(item: dict[str, Any]) -> dict[str, Any]:
    """Mapea un objeto JSON de credencial de Nierika a campos del modelo Credential."""
    return {
        'id': UUID(item['Id']),
        'serial_number': item['SerialNumber'],
        'issued_at': parse_datetime(item.get('IssuedAt')),
        'expiration_date': parse_datetime(item.get('ExpirationDate')),
        'max_expiration_date': parse_datetime(item.get('MaxExpirationDate')),
        'revoked_at': parse_datetime(item.get('RevokedAt')),
        'scan_kind': item.get('ScanKind') or '',
    }


def parse_credentials_page(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Mapea el JSON de una página del catálogo a dicts de campos del modelo."""
    return [parse_credential_item(item) for item in payload.get('items', [])]


class NierikaClient:
    """Cliente HTTP del API de Nierika (urllib stdlib, sin dependencias nuevas).

    El catálogo se descarga completo siguiendo el cursor opaco que devuelve el
    servidor (cursor compuesto `(createdAt, Id)` del lado de Nierika) hasta
    `hasMore=false`. Los mensajes de error jamás incluyen el valor de la key.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        limit: int = DEFAULT_PAGE_LIMIT,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.limit = limit
        self.timeout = timeout

    def iter_credentials(self) -> Iterator[dict[str, Any]]:
        cursor: str | None = None
        while True:
            payload = self.fetch_page(cursor)
            yield from parse_credentials_page(payload)
            if not payload.get('hasMore'):
                return
            cursor = payload.get('cursor')
            if not cursor:
                raise NierikaClientError(
                    'Nierika API reported more items but returned no cursor.'
                )

    def fetch_page(self, cursor: str | None = None) -> dict[str, Any]:
        params: dict[str, str] = {'limit': str(self.limit)}
        if cursor:
            params['cursor'] = cursor
        url = f'{self.base_url}{CREDENTIALS_PATH}?{urllib.parse.urlencode(params)}'
        return self._get_json(url)

    def _get_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(
            url, headers={'Accept': 'application/json', 'X-API-Key': self.api_key}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise NierikaClientError(
                    f'Nierika API rejected the credentials key (HTTP {error.code}).'
                ) from error
            raise NierikaClientError(
                f'Nierika API returned HTTP {error.code}.'
            ) from error
        except urllib.error.URLError as error:
            raise NierikaClientError(
                f'Could not reach Nierika API: {getattr(error, "reason", error)}'
            ) from error
        except (TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise NierikaClientError(
                f'Invalid response from Nierika API: {type(error).__name__}'
            ) from error
