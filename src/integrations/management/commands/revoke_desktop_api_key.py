from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from integrations.models import DesktopApiKey


class Command(BaseCommand):
    help = 'Revoke a desktop API key by its prefix.'

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            '--prefix',
            required=True,
            help='Prefix of the key to revoke (e.g. dsk_7f3a1b).',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        prefix: str = options['prefix']
        key = DesktopApiKey.objects.filter(prefix=prefix).first()
        if key is None:
            raise CommandError(f'No desktop API key found with prefix "{prefix}".')
        if key.revoked_at is not None:
            raise CommandError(
                f'Desktop API key with prefix "{prefix}" is already revoked.'
            )
        key.revoked_at = timezone.now()
        key.save(update_fields=['revoked_at'])
        self.stdout.write(self.style.SUCCESS(
            f'API key "{key.name}" (prefix {prefix}) revoked.'
        ))
