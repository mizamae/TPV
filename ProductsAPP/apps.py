from django.apps import AppConfig
from django.core.cache import cache

class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ProductsAPP'

    def ready(self):
        cache.delete_many(keys=("products_info","consumable_info"))
        from .models import Product, Consumible, VATValue
        try:
            from myTPV.models import SiteSettings
            SETTINGS=SiteSettings.load()
            default,_ = VATValue.objects.get_or_create(**{"id":1,"name":"Standard"})
            if SETTINGS.VAT != default.pc_value:
                default.pc_value = SETTINGS.VAT
                default.save()
            cache.set("DefaultVAT",default.pc_value,None)

            products_info={}
            for product in Product.objects.all():
                products_info[product.id]={"pvp":product.pvp,'stock':product.stock}
            cache.set("products_info",products_info,None)

            consumable_info={}
            for consumable in Consumible.objects.all():
                consumable_info[consumable.id]={'stock':consumable.stock}
            cache.set("consumable_info",consumable_info,None)
        except Exception as exc:
            pass
        