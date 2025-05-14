from django.apps import AppConfig
import logging
logger = logging.getLogger("models")


class UsersappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'UsersAPP'

    def ready(self):
        import UsersAPP.signal_handlers
        # from UsersAPP.tasks import runOnInit
        # runOnInit()

