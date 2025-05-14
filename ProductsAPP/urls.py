from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from . import views

urlpatterns = [
    
    
    path("family/view/<str:code>/<int:id>", views.view_family , name="view_family"),

    path("bill/add", views.add_bill , name="create_bill"),
    path("bill/edit/<str:code>/<int:tab>", views.edit_bill , name="edit_bill"),
    path("bill/view/<str:code>", views.edit_bill , name="view_bill"),
    path("bill/assign_customer/<str:code>", views.assign_customer , name="assign_customer"),
    path("bill/resume/<str:code>", views.resume_bill , name="resume_bill"),
    path("bill/append/<str:code>", views.append_barcode_to_bill , name="append_barcode_to_bill"),
    path("bill/append/<str:code>/<int:id>", views.append_to_bill , name="append_to_bill"),
    path("bill/reduce/<int:id>", views.reduce_bill_position , name="reduce_bill_position"),
    path("bill/close/<str:code>", views.close_bill , name="close_bill"),
    path("bill/delete/<str:code>", views.delete_bill , name="delete_bill"),

    path("check_stocks/", views.check_stock , name="check_stocks"),
    path("check_products/", views.check_products , name="check_products"),
    
]
