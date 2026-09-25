from django.db import models
from django.utils import timezone


class Credential(models.Model):
    """Espejo local de una credencial emitida por Nierika.

    La PK es el UUID asignado por Nierika (no se genera localmente) y solo se
    persisten hechos crudos: sin nombre, matrícula ni datos del titular.
    """

    class Status(models.TextChoices):
        ACTIVE = "Active", "Activa"
        EXPIRED = "Expired", "Expirada"
        REVOKED = "Revoked", "Revocada"

    id = models.UUIDField("Id de Nierika", primary_key=True, editable=False)
    serial_number = models.CharField("Número de serie", max_length=100, db_index=True)
    issued_at = models.DateTimeField("Fecha de emisión", null=True, blank=True)
    expiration_date = models.DateTimeField("Fecha de expiración", null=True, blank=True)
    max_expiration_date = models.DateTimeField("Expiración máxima")
    revoked_at = models.DateTimeField("Fecha de revocación", null=True, blank=True)
    synced_at = models.DateTimeField("Última sincronización", null=True, blank=True)

    class Meta:
        verbose_name = "Credencial"
        verbose_name_plural = "Credenciales"

    def __str__(self) -> str:
        return self.serial_number

    @property
    def status(self) -> Status:
        """Estado derivado con precedencia Revoked > Expired > Active (UTC)."""
        if self.revoked_at is not None:
            return self.Status.REVOKED
        if self.expiration_date is not None and self.expiration_date <= timezone.now():
            return self.Status.EXPIRED
        return self.Status.ACTIVE
