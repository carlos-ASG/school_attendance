from django.db import models
from uuid6 import uuid7


class DesktopApiKey(models.Model):
    """API key emitida por Django para una estación de escritorio.

    El valor completo de la key existe solo en el momento de su generación
    (show-once): aquí se guardan únicamente el prefijo de búsqueda y el hash.
    """

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    name = models.CharField("Etiqueta de estación", max_length=100)
    prefix = models.CharField("Prefijo", max_length=16, db_index=True)
    hash = models.CharField("Hash SHA-256", max_length=64)
    created_at = models.DateTimeField("Creada", auto_now_add=True)
    revoked_at = models.DateTimeField("Revocada", null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "API key de escritorio"
        verbose_name_plural = "API keys de escritorio"

    def __str__(self) -> str:
        return self.name
