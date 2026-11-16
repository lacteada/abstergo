from django.apps import AppConfig


class CasosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.casos"
    verbose_name = "Casos sociales"

    def ready(self):
        from apps.casos import signals  # noqa: F401
