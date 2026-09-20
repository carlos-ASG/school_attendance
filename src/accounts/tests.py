import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase


class UserModelTests(TestCase):
    """Spec: uuid-primary-keys — custom user model with UUID v7 pk."""

    def test_created_user_gets_uuidv7_primary_key(self):
        user = get_user_model().objects.create_user('uuiduser', password='pass')
        self.assertIsInstance(user.pk, uuid.UUID)
        self.assertEqual(user.pk.version, 7)

    def test_get_user_model_resolves_to_accounts_user(self):
        from accounts.models import User

        self.assertIs(get_user_model(), User)
