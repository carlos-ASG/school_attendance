"""Settings for the test suite (used via DJANGO_SETTINGS_MODULE in pyproject.toml).

Identical to config.settings except the database is always in-memory SQLite,
so tests never need the PostgreSQL server from .env (DATABASE_URL) to be
installed or running.
"""

from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
