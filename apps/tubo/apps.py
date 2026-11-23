from django.apps import AppConfig


class TuboConfig(AppConfig):
    name = 'apps.tubo'
    verbose_name = 'Tubo de trabajo'

    def ready(self):
        from apps.tubo import signals  # noqa: F401
