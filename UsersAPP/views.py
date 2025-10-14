from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.template.response import TemplateResponse

# Create your views here.
from .models import User
from .forms import customerForm

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