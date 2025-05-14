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

def home(request):
    now = datetime.datetime.now()
    start_datetime = datetime.datetime(now.year, now.month, now.day)
    todays_bills = BillAccount.objects.filter(date__gt=start_datetime).annotate(order_positions = Count('positions'))
    todays_income=0
    for bill in todays_bills.filter(status = BillAccount.STATUS_PAID):
        todays_income += bill.getPVP()

    return render(request, 'home.html',{'todays_bills':todays_bills,
                                        'todays_income':todays_income})