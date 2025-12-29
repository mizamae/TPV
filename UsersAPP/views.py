from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.template.response import TemplateResponse
from django.db.models import Sum, Count

# Create your views here.
from .models import User, Customer

from .forms import customerForm

from ProductsAPP.models import BillAccount

def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")

        try:
            user = User.objects.get(identifier=identifier)
        except:
            messages.error(request, "User Not Found....")
            return redirect("home")

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Identifier does not match...")

    return TemplateResponse(request, "registration/login.html")

def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("login")

@login_required(login_url="login")
def createCustomer(request):
    

    if request.method == "POST":
        form = customerForm(request.POST)
        if form.is_valid():
            instance=form.save()
            messages.success(request, _("New customer created"))
            return redirect('home')
        
    else:
        form = customerForm()
    return TemplateResponse(request, 'form.html', {'form': form,
                                        'title':_("Create new customer"),
                                        'back_to':'home',})

@login_required(login_url="login")
def viewCustomer(request,id):
    
    customer = Customer.objects.get(id=id)
    if request.method == "POST":
        form = customerForm(request.POST,instance=customer)
        if form.is_valid():
            instance=form.save()
            messages.success(request, _("Customer updated"))
        
    bills = BillAccount.objects.filter(owner=customer).annotate(order_positions = Count('positions'))
    total=0
    total_vat=0
    for bill in bills.filter(status = BillAccount.STATUS_PAID):
        total += bill.total
        total_vat += bill.getVATAmount(withRefunds=False)
    bill_totals={'total':total,'total_vat':total_vat}
    return TemplateResponse(request, 'UsersAPP/customerDetail.html', {'bills':bills,'number':bills.count() if bills else 0,
                                                          'totals':bill_totals,'customer':customer,
                                                          })