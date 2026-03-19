from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore[assignment]
    name = 'applications.home'

    def ready(self):
        import applications.home.signals
        import applications.home.checks
