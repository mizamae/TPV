from django.apps import AppConfig


class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myTPV'

    def ready(self):
        from .models import SiteSettings
        try:
            SiteSettings.runOnInit()
        except Exception as exc:
            pass