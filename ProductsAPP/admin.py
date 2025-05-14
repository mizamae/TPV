from django.contrib import admin
from .models import ProductFamily, Consumible, CombinationPosition, Product, BillAccount, ProductDiscount

# Register your models here.

class PRODUCT_FAMILYAdmin(admin.ModelAdmin):
    list_display = ("name","getNumberOfProducts")
    ordering = ('name',)
    
admin.site.register(ProductFamily, PRODUCT_FAMILYAdmin)

class CONSUMIBLEAdmin(admin.ModelAdmin):
    list_display = ("name","family","stock")
    ordering = ('name',"family")

    def save_model(self, request, obj, form, change):
        create = not obj.id
        if create and obj.generates_product:
            product = Product.objects.create(picture=obj.picture,name=obj.name,barcode=obj.barcode,
                                                 family=obj.family,single_ingredient=True)      
        # else:
        #     pos = CombinationPosition.objects.get(quantity=1,ingredient=obj,product__single_ingredient=True)
        #     pos.product.picture = obj.picture
        #     pos.product.name = obj.name
        #     pos.product.family = obj.family
        #     pos.product.save()

        obj.save()

        if create and obj.generates_product:
            CombinationPosition.objects.get_or_create(product=product,quantity=1,ingredient=obj)

admin.site.register(Consumible, CONSUMIBLEAdmin)

class IngredientInline(admin.TabularInline):
    model = CombinationPosition
    extra = 2 # how many rows to show

class PRODUCTAdmin(admin.ModelAdmin):
    list_display = ("name","family","pvp","cost","stock")
    ordering = ('name',)
    inlines = (IngredientInline,)

admin.site.register(Product, PRODUCTAdmin)

class BILLACCOUNT_Admin(admin.ModelAdmin):
    list_display = ("date","code","owner","get_status_display")
    ordering = ('date',)
    
admin.site.register(BillAccount, BILLACCOUNT_Admin)

class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = ("percent","adminAffectedProducts")
    ordering = ('percent',)
    
admin.site.register(ProductDiscount, ProductDiscountAdmin)