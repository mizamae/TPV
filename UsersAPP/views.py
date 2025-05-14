from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
# Create your views here.
from .models import User
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

    return render(request, "registration/login.html")

def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("login")