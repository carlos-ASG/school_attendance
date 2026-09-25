from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.utils import timezone

from credentials.models import Credential
from integrations.nierika import NierikaClient
from integrations.nierika import NierikaClientError


class Command(BaseCommand):
    help = (
        "Download the full credential catalog from Nierika into the local mirror"
        " (upsert by credential id). No-op when NIERIKA_API_KEY is not configured."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        api_key = settings.NIERIKA_API_KEY
        base_url = settings.NIERIKA_API_BASE_URL
        if not api_key:
            self.stdout.write(
                "NIERIKA_API_KEY is not configured; skipping credential sync.",
            )
            return
        if not base_url:
            raise CommandError(
                "NIERIKA_API_BASE_URL is not configured; cannot sync credentials.",
            )
        client = NierikaClient(base_url, api_key)
        synced_at = timezone.now()
        total = 0
        skipped = 0
        try:
            for fields in client.iter_credentials():
                if fields.get("max_expiration_date") is None:
                    skipped += 1
                    self.stderr.write(
                        self.style.WARNING(
                            "Skipping credential without max expiration"
                            f" date: {fields.get('serial_number')}",
                        ),
                    )
                    continue
                credential_id = fields.pop("id")
                fields["synced_at"] = synced_at
                Credential.objects.update_or_create(id=credential_id, defaults=fields)
                total += 1
        except NierikaClientError as error:
            raise CommandError(f"Credential sync failed: {error}") from error
        self.stdout.write(
            self.style.SUCCESS(f"Synced {total} credentials from Nierika."),
        )
        if skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped {skipped} credentials without max expiration date.",
                ),
            )
