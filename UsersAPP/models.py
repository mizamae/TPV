from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .managers import CustomUserManager
import uuid

class Customer(models.Model):
    first_name = models.CharField(_("Name"), max_length=150)
    last_name = models.CharField(_("Surname"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True)
    phone = models.CharField(_("Phone number"),max_length=15, blank=True)
    cif = models.CharField(_("Tax number"),max_length=15, unique=True)
    saves_paper = models.BooleanField(
        _("Electronic receipt"),
        default=False,
        help_text=_("Desires to receive the receipts electronically"),
    )

    def __str__(self):
        if self.first_name and self.last_name:
            return self.first_name+" "+self.last_name[0]+"."
        elif self.email:
            return self.email
        else:
            return _("Customer ") + str(self.id) 
    
    @staticmethod
    def find(data):
        customer=None
        try:
            customer = Customer.objects.get(phone=data)
        except:
            pass
        try:
            customer = Customer.objects.get(email=data.lower())
        except:
            pass
        try:
            customer = Customer.objects.get(cif=data.upper())
        except:
            pass
        return customer

class User(AbstractBaseUser,PermissionsMixin):
    TYPE_CASHIER=0
    TYPE_MANAGER=10

    TYPES = (
        (TYPE_CASHIER, _("Cashier")),
        (TYPE_MANAGER, _("Manager")),        
    )

    type = models.PositiveSmallIntegerField(verbose_name=_("Type"),default=TYPE_CASHIER,choices=TYPES)
    identifier = models.CharField(editable=True, unique=True,max_length=20)

    first_name = models.CharField(_("First name"), max_length=150, blank=True)
    last_name = models.CharField(_("Last name"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_superuser = models.BooleanField(
        _("superuser"),
        default=False,
        help_text=_(
            "Designates whether this user is a superuser. "
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    USERNAME_FIELD = "identifier"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        permissions=(
            ("can_view_reports", _("Can view reports")),
            ("can_see_historics", _("Can access historic bills")),
            ("can_edit_stock", _("Can manually modify stock values")),
            ("can_edit_prices", _("Can manually modify prices")),
            ("can_add_customer", _("Can create a new customer")),
            ("can_add_billaccount", _("Can create a new bill"))
        )

    def __str__(self):
        return self.first_name + " " + self.last_name

    def shortName(self,):
        try:
            if self.first_name and self.last_name:
                return self.first_name[0]+"."+self.last_name
            else:
                return _("Missing name of the user")
        except:
            return _("Missing name of the user")
                
    def getGroups(self,):
        return self.groups.all()

    @admin.display(description=_("Profiles"))
    def printGroups(self,):
        groups=self.getGroups()
        if groups:
            if len(groups) == 1:
                return str(groups[0])
            else:
                listgroups=str(groups[0])
            for group in groups[1:]:
                listgroups+=", "+str(group)
            return listgroups
        else:
            return ""
        
    @admin.display(description=_("Type"))
    def getType(self) -> str:
        return self.get_type_display()
    
    @staticmethod
    def getStaffEmails():
        staff = User.objects.filter(is_staff=True)
        recipients=[]
        for user in staff:
            if user.email:
                recipients.append(user.email)
        return recipients
    
    @classmethod
    def loadDefaultObjects(cls):
        import json
        import os
        file = os.path.join(os.path.dirname(__file__),'users.json')
        with open(file, 'r', encoding='utf-8') as f:
            users = json.load(f)

        for user in users:
            try:
                cls.objects.get(username=user['username'])
            except cls.DoesNotExist:
                X , created = cls.objects.get_or_create(username=user['username'],
                                                    first_name=user['first_name'],last_name=user['last_name'],
                                                    email=user['email'],
                                                    type=cls.TYPE_MANAGER if user['type']=="manager" else cls.TYPE_CASHIER,
                                                )
                if created:
                    X.save()
                    

