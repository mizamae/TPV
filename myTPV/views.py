from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils.translation import gettext as _
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
import datetime

from django.db.models import Q
User=get_user_model()

from ProductsAPP.models import BillAccount
from .forms import reportForm, REPORT_TYPE_SALES, REPORT_TYPE_PRODUCTS, siteSettingsForm
from .models import SiteSettings
from UsersAPP.models import Customer
from ProductsAPP.models import Consumible, Product, BillAccount
def home(request):
    now = datetime.datetime.now()
    start_datetime = datetime.datetime(now.year, now.month, now.day)
    todays_bills = BillAccount.objects.filter(createdOn__gt=start_datetime).annotate(order_positions = Count('positions'))
    todays_income=0
    for bill in todays_bills.filter(status = BillAccount.STATUS_PAID):
        todays_income += bill.total
    badge={}
    badge["customers"]=str(Customer.objects.count()) + _(" customers")
    badge["stock"]=str(Consumible.objects.count()) + _(" references")
    badge["prices"]=str(Product.objects.count()) + _(" products")
    badge["reports"]=""
    badge["historic"]=str(BillAccount.objects.count()) + _(" bills")
    return render(request, 'home.html',{'todays_bills':todays_bills,
                                        'todays_income':round(todays_income,2),
                                        'badge':badge})

def reports_home(request):
    if request.method == "POST":
        form=reportForm(request.POST)
        if form.is_valid():
            report={}
            report['type'] = form.cleaned_data['_type']
            report['to'] = form.cleaned_data['_to'] if form.cleaned_data['_to'] else datetime.datetime.today().date()+datetime.timedelta(days=1)
            report['from'] = form.cleaned_data['_from'] if form.cleaned_data['_from'] else report['to']-datetime.timedelta(days=365)
            
            if report['type']==REPORT_TYPE_SALES:
                from ProductsAPP.reports import SalesReport
                titles,figures = SalesReport(_from=report['from'],_to=report['to'])
                heading = _("Sales report") 
            elif report['type']==REPORT_TYPE_PRODUCTS:
                from ProductsAPP.reports import ProductsReport
                titles,figures = ProductsReport(_from=report['from'],_to=report['to'])
                heading = _("Products report") 
            return render(request, 'reportWithFigs.html', {'titles':titles,'figures':figures, 'heading':heading})
            
    else:
        form=reportForm()

    return render(request, 'form.html', {'form': form,
                                        'title':_("View report"),
                                        'back_to':'home',})
@login_required
def siteSettings(request):
    if request.method == "POST":
        form=siteSettingsForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form=siteSettingsForm(instance = SiteSettings.load())

    return render(request, 'form.html', {'form': form,
                                        'title':_("Site settings"),
                                        'back_to':'home',})