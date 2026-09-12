import importlib.util

from django.apps import apps
from django.test.runner import DiscoverRunner


class SrcLayoutDiscoverRunner(DiscoverRunner):
    """Discover tests in app packages that live under src/."""

    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            test_labels = [
                f'{app_config.name}.tests'
                for app_config in apps.get_app_configs()
                if importlib.util.find_spec(f'{app_config.name}.tests') is not None
            ]
        return super().build_suite(test_labels, **kwargs)
