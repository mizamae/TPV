from django.contrib import admin
from .models import VATValue, ProductFamily, Manufacturer, Consumible, CombinationPosition, Product, BillAccount, ProductDiscount

# Register your models here.

class VATValueAdmin(admin.ModelAdmin):
    list_display = ("name","pc_value")
    ordering = ('name',)
    
admin.site.register(VATValue, VATValueAdmin)

class PRODUCT_FAMILYAdmin(admin.ModelAdmin):
    list_display = ("name","getNumberOfProducts")
    ordering = ('name',)
    
admin.site.register(ProductFamily, PRODUCT_FAMILYAdmin)

class MANUFACTURERAdmin(admin.ModelAdmin):
    list_display = ("name","getNumberOfProducts")
    ordering = ('name',)
    
admin.site.register(Manufacturer, MANUFACTURERAdmin)

class CONSUMIBLEAdmin(admin.ModelAdmin):
    list_display = ("name","family","stock")
    ordering = ('name',"family")            

admin.site.register(Consumible, CONSUMIBLEAdmin)

class IngredientInline(admin.TabularInline):
    model = CombinationPosition
    extra = 2 # how many rows to show

class PRODUCTAdmin(admin.ModelAdmin):
    list_display = ("name","family","price","cost","stock")
    ordering = ('name',)
    inlines = (IngredientInline,)
    exclude = ('single_ingredient',)

admin.site.register(Product, PRODUCTAdmin)

class BILLACCOUNT_Admin(admin.ModelAdmin):
    list_display = ("createdOn","code","owner","get_status_display")
    ordering = ('createdOn',)
    
admin.site.register(BillAccount, BILLACCOUNT_Admin)

class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = ("percent","adminAffectedProducts")
    ordering = ('percent',)
    
admin.site.register(ProductDiscount, ProductDiscountAdmin)