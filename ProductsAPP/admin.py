from django.contrib import admin
from .models import VATValue, ProductFamily, Manufacturer, Consumible, CombinationPosition, Product, BillAccount, \
                    ProductDiscount, ProductPromotion, Refund, DiscountVoucher

from .tasks import sendBillReceipt
# Register your models here.

class DiscountVoucherAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(DiscountVoucher, DiscountVoucherAdmin)

class RefundAdmin(admin.ModelAdmin):
    list_display = ("bill_pos__bill__code","bill_pos",)
    list_filter = ["bill_pos__bill__code",]
    ordering = ("bill_pos__bill__code",)
    
admin.site.register(Refund, RefundAdmin)

class VATValueAdmin(admin.ModelAdmin):
    list_display = ("name","pc_value")
    ordering = ('name',)
    
admin.site.register(VATValue, VATValueAdmin)

class PRODUCT_FAMILYAdmin(admin.ModelAdmin):
    list_display = ("name","getNumberOfProducts")
    ordering = ('name',)
    
    def save_model(self, request, obj, form, change):
        update_fields = []

        if change:
            for field in form.fields:
                if form.initial[field] != form.cleaned_data[field]:
                    update_fields.append(field)
            obj.save(update_fields=update_fields)
        else:
            obj.save()

admin.site.register(ProductFamily, PRODUCT_FAMILYAdmin)

class MANUFACTURERAdmin(admin.ModelAdmin):
    list_display = ("name","getNumberOfProducts")
    ordering = ('name',)
    
admin.site.register(Manufacturer, MANUFACTURERAdmin)

class CONSUMIBLEAdmin(admin.ModelAdmin):
    list_display = ("name","family","stock")
    list_filter = ["manufacturer", "family"]
    ordering = ('name',"family")  
    save_as = True          

admin.site.register(Consumible, CONSUMIBLEAdmin)

class IngredientInline(admin.TabularInline):
    model = CombinationPosition
    extra = 2 # how many rows to show

class PRODUCTAdmin(admin.ModelAdmin):
    list_display = ("name","family","price","cost","stock")
    list_filter = ["family"]
    
    ordering = ('name',)
    inlines = (IngredientInline,)
    exclude = ('single_ingredient',)

    def save_model(self, request, obj, form, change):
        update_fields = []

        if change:
            for field in form.fields:
                if form.initial[field] != form.cleaned_data[field]:
                    update_fields.append(field)
            obj.save(update_fields=update_fields)
        else:
            obj.save()

        
        
admin.site.register(Product, PRODUCTAdmin)

class BILLACCOUNT_Admin(admin.ModelAdmin):
    list_display = ("createdOn","code","owner","get_status_display")
    ordering = ('createdOn',)
    actions=['sendToCustomer',]
    
    def sendToCustomer(self, request, queryset):
        for item in queryset:
            if item.owner:
                sendBillReceipt.delay(billData=item.toJSON())
    
admin.site.register(BillAccount, BILLACCOUNT_Admin)

class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = ("percent","adminAffectedProducts")
    ordering = ('percent',)
    
admin.site.register(ProductDiscount, ProductDiscountAdmin)

class ProductPromotionAdmin(admin.ModelAdmin):
    list_display = ("__str__","adminAffectedProducts")


    
admin.site.register(ProductPromotion, ProductPromotionAdmin)