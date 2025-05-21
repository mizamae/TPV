from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from . import views

urlpatterns = [
    
    path("bill/add", views.add_bill , name="MaterialsAPP_create_bill"),
    path("bill/edit/<str:code>/<int:tab>", views.edit_bill , name="MaterialsAPP_edit_bill"),
    path("bill/edit/<str:code>/<int:tab>/<int:billPos>", views.edit_bill , name="MaterialsAPP_edit_billPos"),
    path("bill/MaterialsAPP_assign_customer/<str:code>", views.assign_customer , name="MaterialsAPP_assign_customer"),
    path("bill/resume/<str:code>", views.resume_bill , name="MaterialsAPP_resume_bill"),
    path("bill/append/<str:code>", views.append_barcode_to_bill , name="MaterialsAPP_append_barcode_to_bill"),
    path("bill/append/<str:code>/<int:id>", views.append_to_bill , name="MaterialsAPP_append_to_bill"),
    path("bill/reduce/<int:id>", views.reduce_bill_position , name="MaterialsAPP_reduce_bill_position"),
    path("bill/close/<str:code>", views.close_bill , name="MaterialsAPP_close_bill"),
    path("bill/delete/<str:code>", views.delete_bill , name="MaterialsAPP_delete_bill"),
    path("bill/billposition/setmultiplier/<int:id>", views.setMultiplier_billPosition , name="ProductsAPP_billPosition_setMultiplier"),
    path("bill/historics", views.historics_home , name="MaterialsAPP_historics_home"),
    path("bill/print/<str:code>", views.print_bill , name="MaterialsAPP_print_bill"),

    path("MaterialsAPP_check_stocks/", views.check_stock , name="MaterialsAPP_check_stocks"),
    path("MaterialsAPP_check_products/", views.check_products , name="MaterialsAPP_check_products"),
    
]
