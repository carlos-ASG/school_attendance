from django.apps import AppConfig


class SchoolConfig(AppConfig):
    name = 'school'
    verbose_name = 'Asistencia Escolar'

    def ready(self):
        from . import components  # noqa: F401
