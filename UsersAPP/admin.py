from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User , Customer

class CustomerAdmin(admin.ModelAdmin):
    list_display = ("first_name","last_name","email","phone","cif","saves_paper")

admin.site.register(Customer, CustomerAdmin)

class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = User
        exclude = ()

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        exclude=()

class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    model = User

    list_display = ("first_name","last_name","getType","printGroups")
    ordering = ('first_name',)

            
    fieldsets = (
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
                )
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        })
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('identifier',),
        }),
    )

admin.site.register(User, UserAdmin)