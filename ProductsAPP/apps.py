from django.apps import AppConfig
from django.core.cache import cache

class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ProductsAPP'

    def ready(self):
        from .models import VATValue
        try:
            default = VATValue.objects.get_or_create(**{"id":1,"name":"Standard","pc_value":21})
        except Exception as exc:
            pass
        cache.clear()