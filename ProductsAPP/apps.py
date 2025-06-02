from django.apps import AppConfig
from django.core.cache import cache

class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ProductsAPP'

    def ready(self):
        cache.clear()
        from .models import VATValue
        try:
            default,_ = VATValue.objects.get_or_create(**{"id":1,"name":"Standard","pc_value":21})
            cache.set("DefaultVAT",default.pc_value,None)
        except Exception as exc:
            pass
        