import json
 
from django import template

from ProductsAPP.models import BillAccount,Consumible

register = template.Library()

@register.filter
def get_at_index(list, index):
    return list[index]
 
@register.filter(name='canCreateBill')
def canCreateBill(user):
    return BillAccount.can_createBill(user)

@register.simple_tag
def get_monthly_consumption(consumible,month,year):
    return consumible.get_monthly_consumption(month=month,year=year)

@register.simple_tag
def get_monthly_ingress(consumible,month,year):
    return round(consumible.get_monthly_consumption(month=month,year=year)*consumible.pvp,2)

@register.simple_tag
def get_monthly_cost(consumible,month,year):
    return round(consumible.get_monthly_consumption(month=month,year=year)*consumible.cost,2)