from django.contrib import admin

from .models import SiteSettings

class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("SHOP_NAME",)
    ordering = ('SHOP_NAME',)

    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(SiteSettings, SiteSettingsAdmin)