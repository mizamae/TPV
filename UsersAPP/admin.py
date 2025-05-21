from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User , Customer
from .forms import userForm

class CustomerAdmin(admin.ModelAdmin):
    list_display = ("first_name","last_name","email","phone","cif","saves_paper")

admin.site.register(Customer, CustomerAdmin)


class UserAdmin(admin.ModelAdmin):
    add_form = userForm
    form = userForm


    list_display = ("first_name","last_name",'identifier')
    ordering = ('first_name',)


admin.site.register(User, UserAdmin)