from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ProductsAPP'

    def ready(self):
        from .models import VATValue
        default = VATValue.objects.get_or_create(**{"id":1,"name":"Standard","pc_value":21})
