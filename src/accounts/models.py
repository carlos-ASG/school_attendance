from django.contrib.auth.models import AbstractUser
from django.db import models
from uuid6 import uuid7


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
