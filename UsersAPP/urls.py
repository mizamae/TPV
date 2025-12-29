from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from . import views

urlpatterns = [
    path("login/", views.login_view , name="login"),
    path("logout/", views.logout_view , name="logout"),
    
    path("customers/create", views.createCustomer , name="UsersAPP_create_customer"),
    path("customers/view/<int:id>", views.viewCustomer , name="UsersAPP_view_customer"),
]
