from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils.translation import gettext as _
from django.urls import reverse
from django.http import HttpResponse

import json
from .models import BillAccount, Product, ProductFamily, BillPosition, Consumible
from .forms import paymentMethodsForm, StockFormSet, ProductFormSet, barcode2BillForm

from UsersAPP.forms import findCustomerForm
from UsersAPP.models import Customer

@login_required(login_url="login")
def add_bill(request):
    bill=BillAccount.create(createdBy=request.user)
    return redirect('MaterialsAPP_edit_bill',code=bill.code,tab=0)

@login_required(login_url="login")
def edit_bill(request,code,tab=None,billPos=None):
    bill=BillAccount.objects.get(code=code)
    productFamilies=ProductFamily.objects.all()
    productfamilies_tabs=[]
    if tab is None or tab == 'None':
        tab=0
    else:
        tab=int(tab)
    
    if billPos is None or billPos == 'None':
        billPos=None
    else:
        billPos=BillPosition.objects.get(id=int(billPos))

    for i,_type in enumerate(productFamilies):
        productfamilies_tabs.append({'name':_type.name,'id':_type.id,'active':_type.id==tab,'items':Product.objects.filter(family=_type).order_by("name")})

    if tab==0:
        productfamilies_tabs[0]['active']=True

    return render(request, 'bill.html',{'bill' : bill,
                                        #'categories':non_emptyFamilies,
                                        'productfamilies_tabs':productfamilies_tabs,
                                        'legend':"Categorías",
                                        "findCustomerForm":findCustomerForm(),
                                        "barcode2BillForm":barcode2BillForm(),
                                        "billPos":billPos
                                        })


@login_required(login_url="login")
def assign_customer(request,code):
    bill=BillAccount.objects.get(code=code)

    if request.method == 'POST':
        form = findCustomerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data['data']
            customer = Customer.find(data=data)
            if customer:
                bill.owner = customer
                bill.save(update_fields=['owner',])
            else:
                messages.info(request, _("No customer found "))
                    
    return redirect('MaterialsAPP_edit_bill',code=bill.code,tab=0)

@login_required(login_url="login")
def append_barcode_to_bill(request,code):
    bill=BillAccount.objects.get(code=code)
    if request.method == 'POST':
        form = barcode2BillForm(request.POST)
        if form.is_valid():
            barcode = form.cleaned_data['barcode']
            try:
                product=Product.objects.get(barcode=barcode)
                return redirect('MaterialsAPP_append_to_bill',code=bill.code,id=product.id)
            except:
                pass            
    messages.error(request, _("The barcode introduced is not registered"))
    return redirect('MaterialsAPP_edit_bill',code = bill.code,tab=0) 

@login_required(login_url="login")
def append_to_bill(request,code,id):
    bill=BillAccount.objects.get(code=code)
    product=Product.objects.get(id=id)
    billPos=bill.add_bill_position(product=product,quantity=1)

    return redirect('MaterialsAPP_edit_billPos',code=bill.code,tab=product.family.id,billPos=billPos.id)

@login_required(login_url="login")
def reduce_bill_position(request,id):
    bill_pos=BillPosition.objects.get(id=id)
    family=bill_pos.product.family
    bill_pos.reduce_quantity(quantity=1)
    return redirect('MaterialsAPP_edit_bill',code=bill_pos.bill.code,tab=family.id)

@login_required(login_url="login")
def resume_bill(request,code):
    bill=BillAccount.objects.get(code=code)
    paymentForm = paymentMethodsForm(instance=bill)
    return render(request, 'bill_resume.html',{'bill' : bill,'paymentForm':paymentForm})

@login_required(login_url="login")
def close_bill(request,code):
    bill=BillAccount.objects.get(code=code)
    if request.method == 'POST':
        paymentForm = paymentMethodsForm(request.POST,instance=bill)
        if paymentForm.is_valid():
            paymentForm.save()
            if bill.bill_positions.all().count() > 0:
                bill.close()
            else:
                bill.delete()
        else:
            messages.error(request, _("The payment method should be defined"))
            return redirect('MaterialsAPP_resume_bill',code = bill.code)

    return redirect('home')

@login_required(login_url="login")
def delete_bill(request,code):
    bill=BillAccount.objects.get(code=code)
    bill.delete()
    return redirect('home')

def setMultiplier_billPosition(request,id):
    ''' This is an AJAX request, return data for the request to proceed '''
    if request.method == 'POST':
        value = json.loads(request.body.decode())['value']
        billPosition = BillPosition.objects.get(id=id)
        billPosition.increase_quantity(quantity=value-1)
        response={'url':reverse('MaterialsAPP_edit_bill',kwargs={'code':billPosition.bill.code,'tab':billPosition.product.family.id})}
    else:
        response=None
    return HttpResponse(json.dumps(response), content_type='application/json')

# Create your views here.
@login_required(login_url="login")
def check_stock(request):
    user = request.user
    if request.method == 'POST':
        stock_formset = StockFormSet(request.POST,queryset=Consumible.objects.filter(infinite=False))
        if stock_formset.is_valid():
            stock_formset.save()
            messages.success(request, _("The stock has been updated"))
            return redirect('home')
        else:
            for error in list(stock_formset.errors.values()):
                messages.error(request, error)

    stock_formset = StockFormSet(queryset=Consumible.objects.filter(infinite=False))
    stock_value = Consumible.get_stock_value()
    return render(request, 'stock.html', {'stock_formset': stock_formset,
                                          'stock_value':stock_value})

@login_required(login_url="login")
def check_products(request):
    user = request.user
    if request.method == 'POST':
        product_formset = ProductFormSet(request.POST)
        if product_formset.is_valid():
            product_formset.save()
            messages.success(request, _("Product prices have been updated"))
            return redirect('home')
        else:
            for error in list(product_formset.errors.values()):
                messages.error(request, error)

    product_formset = ProductFormSet()
    return render(request, 'products.html', {'product_formset': product_formset,})