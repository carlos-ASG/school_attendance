from django.db import models
from uuid6 import uuid7


class UUIDv7Model(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)

    class Meta:
        abstract = True
