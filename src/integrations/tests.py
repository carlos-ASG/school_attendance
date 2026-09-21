import hashlib
import io
import re
import urllib.error
import uuid
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from credentials.models import Credential

from .keys import KEY_ALPHABET, extract_prefix, generate_key, hash_key
from .models import DesktopApiKey
from .nierika import NierikaClient, NierikaClientError, parse_credentials_page


class NierikaSettingsTests(TestCase):
    def test_variables_default_to_empty_strings(self) -> None:
        self.assertEqual(settings.NIERIKA_API_BASE_URL, '')
        self.assertEqual(settings.NIERIKA_API_KEY, '')

    def test_variables_are_strings_when_unset(self) -> None:
        self.assertIsInstance(settings.NIERIKA_API_BASE_URL, str)
        self.assertIsInstance(settings.NIERIKA_API_KEY, str)


def nierika_item(serial: str, **overrides: object) -> dict[str, object]:
    item: dict[str, object] = {
        'Id': str(uuid.uuid4()),
        'SerialNumber': serial,
        'IssuedAt': '2026-01-15T10:30:00Z',
        'ExpirationDate': '2027-12-31T23:59:59Z',
        'MaxExpirationDate': None,
        'RevokedAt': None,
        'ScanKind': 'QR',
    }
    item.update(overrides)
    return item


class ParseCredentialsPageTests(SimpleTestCase):
    def test_maps_pascal_case_payload_to_model_fields(self) -> None:
        fields = parse_credentials_page({'items': [nierika_item('SN-1')]})[0]
        self.assertEqual(fields['serial_number'], 'SN-1')
        self.assertEqual(fields['scan_kind'], 'QR')
        self.assertEqual(fields['issued_at'].year, 2026)
        self.assertIsNone(fields['revoked_at'])
        self.assertIsNone(fields['max_expiration_date'])
        uuid.UUID(str(fields['id']))

    def test_missing_scan_kind_defaults_to_empty(self) -> None:
        item = nierika_item('SN-2', ScanKind=None)
        fields = parse_credentials_page({'items': [item]})[0]
        self.assertEqual(fields['scan_kind'], '')


class NierikaClientTests(SimpleTestCase):
    CLIENT_KEY = 'nkb_super_secret_value'

    def make_client(self) -> NierikaClient:
        return NierikaClient(
            'https://nierika.example.com', self.CLIENT_KEY, limit=2, timeout=5
        )

    def test_follows_server_cursor_until_has_more_false(self) -> None:
        client = self.make_client()
        pages = [
            {
                'items': [nierika_item('SN-1'), nierika_item('SN-2')],
                'hasMore': True,
                'cursor': '2026-01-15T10:30:00Z|id-2',
            },
            {'items': [nierika_item('SN-3')], 'hasMore': False},
        ]
        with mock.patch.object(client, 'fetch_page', side_effect=pages) as fetch:
            serials = [f['serial_number'] for f in client.iter_credentials()]
        self.assertEqual(serials, ['SN-1', 'SN-2', 'SN-3'])
        self.assertEqual(
            fetch.call_args_list,
            [mock.call(None), mock.call('2026-01-15T10:30:00Z|id-2')],
        )

    def test_has_more_without_cursor_raises(self) -> None:
        client = self.make_client()
        page = {'items': [nierika_item('SN-1')], 'hasMore': True}
        with mock.patch.object(client, 'fetch_page', return_value=page):
            with self.assertRaises(NierikaClientError):
                list(client.iter_credentials())

    def _fetch_with_error(self, error: Exception) -> NierikaClientError:
        client = self.make_client()
        with mock.patch(
            'integrations.nierika.urllib.request.urlopen', side_effect=error
        ):
            with self.assertRaises(NierikaClientError) as ctx:
                client.fetch_page('cursor-1')
        return ctx.exception

    def test_http_401_error_never_includes_key(self) -> None:
        error = urllib.error.HTTPError(
            'https://nierika.example.com/x', 401, 'Unauthorized', {}, io.BytesIO(b'')
        )
        message = str(self._fetch_with_error(error))
        self.assertIn('401', message)
        self.assertNotIn(self.CLIENT_KEY, message)

    def test_http_500_error(self) -> None:
        error = urllib.error.HTTPError(
            'https://nierika.example.com/x', 500, 'Server Error', {}, io.BytesIO(b'')
        )
        message = str(self._fetch_with_error(error))
        self.assertIn('500', message)
        self.assertNotIn(self.CLIENT_KEY, message)

    def test_unreachable_server_error_never_includes_key(self) -> None:
        error = urllib.error.URLError(ConnectionRefusedError(111))
        message = str(self._fetch_with_error(error))
        self.assertNotIn(self.CLIENT_KEY, message)

    def test_request_sends_api_key_header_and_params(self) -> None:
        client = self.make_client()
        response = io.BytesIO(b'{"items": [], "hasMore": false}')
        with mock.patch(
            'integrations.nierika.urllib.request.urlopen'
        ) as urlopen, mock.patch('integrations.nierika.urllib.request.Request') as req:
            urlopen.return_value.__enter__.return_value = response
            client.fetch_page('cursor-1')
        url = req.call_args.args[0]
        headers = req.call_args.kwargs['headers']
        self.assertIn('limit=2', url)
        self.assertIn('cursor=cursor-1', url)
        self.assertIn('/api/integrations/me/credentials', url)
        self.assertEqual(headers['X-API-Key'], self.CLIENT_KEY)


NO_KEY_SETTINGS = dict(NIERIKA_API_BASE_URL='', NIERIKA_API_KEY='')
KEY_SETTINGS = dict(
    NIERIKA_API_BASE_URL='https://nierika.example.com',
    NIERIKA_API_KEY='nkb_test_key',
)


class SyncCommandNoKeyTests(TestCase):
    @override_settings(**NO_KEY_SETTINGS)
    def test_noop_without_api_key(self) -> None:
        out = io.StringIO()
        with mock.patch(
            'integrations.management.commands.sync_nierika_credentials.NierikaClient',
            side_effect=AssertionError('HTTP client must not be built without key'),
        ):
            call_command('sync_nierika_credentials', stdout=out)
        self.assertIn('skipping credential sync', out.getvalue())
        self.assertEqual(Credential.objects.count(), 0)


def make_sync_fields(serial: str, credential_id: uuid.UUID | None = None) -> dict:
    return {
        'id': credential_id or uuid.uuid4(),
        'serial_number': serial,
        'issued_at': timezone.now(),
        'expiration_date': timezone.now() + timedelta(days=365),
        'max_expiration_date': None,
        'revoked_at': None,
        'scan_kind': 'QR',
    }


@override_settings(**KEY_SETTINGS)
class SyncCommandWithKeyTests(TestCase):
    def _sync(self, fields: list[dict]) -> str:
        out = io.StringIO()
        with mock.patch(
            'integrations.management.commands.sync_nierika_credentials.NierikaClient'
        ) as client_class:
            client_class.return_value.iter_credentials.return_value = iter(fields)
            call_command('sync_nierika_credentials', stdout=out)
        client_class.assert_called_once_with(
            'https://nierika.example.com', 'nkb_test_key'
        )
        return out.getvalue()

    def test_upserts_every_field_and_fixes_synced_at(self) -> None:
        fields = [make_sync_fields('SN-1'), make_sync_fields('SN-2')]
        expected = [(data['id'], data['serial_number']) for data in fields]
        output = self._sync(fields)
        self.assertEqual(Credential.objects.count(), 2)
        for credential_id, serial in expected:
            credential = Credential.objects.get(id=credential_id)
            self.assertEqual(credential.serial_number, serial)
            self.assertEqual(credential.scan_kind, 'QR')
            self.assertIsNotNone(credential.synced_at)
        self.assertIn('Synced 2 credentials', output)

    def test_rerun_is_idempotent(self) -> None:
        credential_id = uuid.uuid4()
        self._sync([make_sync_fields('SN-1', credential_id=credential_id)])
        self._sync([make_sync_fields('SN-1', credential_id=credential_id)])
        self.assertEqual(Credential.objects.count(), 1)
        row = Credential.objects.get(id=credential_id)
        self.assertEqual(row.serial_number, 'SN-1')

    def test_updates_stale_row(self) -> None:
        stale = Credential.objects.create(
            id=uuid.uuid4(),
            serial_number='SN-OLD',
            expiration_date=timezone.now() - timedelta(days=1),
            synced_at=timezone.now() - timedelta(days=7),
        )
        fresh = make_sync_fields('SN-NEW', credential_id=stale.id)
        fresh['revoked_at'] = timezone.now()
        self._sync([fresh])
        self.assertEqual(Credential.objects.count(), 1)
        row = Credential.objects.get(id=stale.id)
        self.assertEqual(row.serial_number, 'SN-NEW')
        self.assertEqual(row.revoked_at, fresh['revoked_at'])
        self.assertGreater(row.synced_at, stale.synced_at)
        self.assertEqual(row.status, Credential.Status.REVOKED)

    def test_server_failure_raises_command_error_without_leaking_key(self) -> None:
        with mock.patch(
            'integrations.management.commands.sync_nierika_credentials.NierikaClient'
        ) as client_class:
            client_class.return_value.iter_credentials.side_effect = (
                NierikaClientError('Nierika API returned HTTP 503.')
            )
            with self.assertRaises(CommandError) as ctx:
                call_command(
                    'sync_nierika_credentials', stdout=io.StringIO()
                )
        message = str(ctx.exception)
        self.assertIn('503', message)
        self.assertNotIn('nkb_test_key', message)


class KeysModuleTests(SimpleTestCase):
    def test_key_format_dsk_body_base62(self) -> None:
        key = generate_key()
        self.assertTrue(key.startswith('dsk_'))
        body = key.removeprefix('dsk_')
        self.assertEqual(len(body), 43)
        self.assertTrue(all(char in KEY_ALPHABET for char in body))

    def test_keys_are_unique(self) -> None:
        self.assertNotEqual(generate_key(), generate_key())

    def test_extract_prefix_takes_first_ten_chars(self) -> None:
        key = 'dsk_' + 'A1b2C3d4e5' + 'x' * 33
        self.assertEqual(extract_prefix(key), 'dsk_A1b2C3')

    def test_hash_matches_sha256_hex(self) -> None:
        self.assertEqual(hash_key('dsk_test'), hashlib.sha256(b'dsk_test').hexdigest())
        self.assertEqual(len(hash_key('dsk_test')), 64)


class CreateDesktopApiKeyCommandTests(TestCase):
    FULL_KEY_PATTERN = re.compile(r'dsk_[A-Za-z0-9]{43}')

    def _create(self) -> tuple[str, DesktopApiKey]:
        out = io.StringIO()
        call_command(
            'create_desktop_api_key', name='estacion-direccion', stdout=out
        )
        return out.getvalue(), DesktopApiKey.objects.get()

    def test_creates_row_and_prints_key_once(self) -> None:
        output, row = self._create()
        printed_key = self.FULL_KEY_PATTERN.search(output)
        self.assertIsNotNone(printed_key)
        full_key = printed_key.group(0)
        self.assertEqual(row.name, 'estacion-direccion')
        self.assertEqual(row.prefix, extract_prefix(full_key))
        self.assertEqual(row.hash, hash_key(full_key))
        self.assertIsNone(row.revoked_at)
        self.assertIn(row.prefix, output)
        self.assertIn('only time the full key is shown', output)

    def test_full_key_never_stored_in_clear(self) -> None:
        output, row = self._create()
        full_key = self.FULL_KEY_PATTERN.search(output).group(0)
        self.assertNotEqual(row.hash, full_key)
        self.assertNotIn(full_key, row.hash)
        stored = list(
            DesktopApiKey.objects.values('name', 'prefix', 'hash', 'created_at')
        )
        self.assertEqual(len(stored), 1)
        self.assertNotIn(full_key, str(stored[0]))


class RevokeDesktopApiKeyCommandTests(TestCase):
    def _make_key(self, name: str = 'estacion-x') -> tuple[str, DesktopApiKey]:
        key = generate_key()
        row = DesktopApiKey.objects.create(
            name=name, prefix=extract_prefix(key), hash=hash_key(key)
        )
        return key, row

    def test_revokes_active_key(self) -> None:
        key, row = self._make_key()
        before = timezone.now()
        out = io.StringIO()
        call_command(
            'revoke_desktop_api_key', '--prefix', extract_prefix(key), stdout=out
        )
        row.refresh_from_db()
        self.assertIsNotNone(row.revoked_at)
        self.assertGreaterEqual(row.revoked_at, before)
        self.assertIn('revoked', out.getvalue())

    def test_revoking_already_revoked_key_fails(self) -> None:
        key, row = self._make_key()
        call_command('revoke_desktop_api_key', '--prefix', extract_prefix(key))
        row.refresh_from_db()
        first = row.revoked_at
        with self.assertRaises(CommandError) as ctx:
            call_command(
                'revoke_desktop_api_key', '--prefix', extract_prefix(key)
            )
        self.assertIn('already revoked', str(ctx.exception))
        row.refresh_from_db()
        self.assertEqual(row.revoked_at, first)

    def test_unknown_prefix_fails(self) -> None:
        with self.assertRaises(CommandError) as ctx:
            call_command('revoke_desktop_api_key', '--prefix', 'dsk_unknown0')
        self.assertIn('No desktop API key found', str(ctx.exception))


class DesktopApiKeyTests(TestCase):
    def test_creation_defaults(self) -> None:
        key = DesktopApiKey.objects.create(
            name='estacion-direccion', prefix='dsk_abc12', hash='a' * 64
        )
        key.refresh_from_db()
        self.assertEqual(key.name, 'estacion-direccion')
        self.assertEqual(key.prefix, 'dsk_abc12')
        self.assertEqual(key.hash, 'a' * 64)
        self.assertIsNotNone(key.created_at)
        self.assertIsNone(key.revoked_at)
