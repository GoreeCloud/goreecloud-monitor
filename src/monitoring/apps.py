from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitoring"

    def ready(self) -> None:
        # Import signal receivers only after Django's app registry is ready.
        from . import signals  # noqa: F401
