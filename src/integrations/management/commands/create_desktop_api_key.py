from typing import Any

from django.core.management.base import BaseCommand

from integrations.keys import extract_prefix, generate_key, hash_key
from integrations.models import DesktopApiKey


class Command(BaseCommand):
    help = 'Generate a desktop API key. The full key is printed once (show-once).'

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            '--name',
            required=True,
            help='Station label stored with the key.',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        name: str = options['name']
        key = generate_key()
        DesktopApiKey.objects.create(
            name=name, prefix=extract_prefix(key), hash=hash_key(key)
        )
        self.stdout.write(self.style.SUCCESS(
            f'API key for "{name}" created (prefix {extract_prefix(key)}).'
        ))
        self.stdout.write(self.style.WARNING(
            'Save it now: this is the only time the full key is shown.'
        ))
        self.stdout.write(key)
