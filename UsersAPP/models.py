from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from .managers import CustomUserManager

class CustomerProfile(models.Model):
    class Meta:
        verbose_name = _('Customer profile')
        verbose_name_plural = _('Customer profiles')

    PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]

    name = models.CharField(_("Name"), max_length=150)
    percent = models.FloatField(default=0,verbose_name=_("Percentage over bill's total"),validators=PERCENTAGE_VALIDATOR)

    def __str__(self):
        return self.name
    
    @admin.display(description=_("Customers"))
    def adminAffectedCustomers(self,):
        return list(map(str,self.affectedCustomers))
    
    @property
    def affectedCustomers(self):
        return self.customers.all()
    
class Customer(models.Model):
    class Meta:
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')

    first_name = models.CharField(_("Name"), max_length=150)
    last_name = models.CharField(_("Surname"), max_length=150, blank=True)
    email = models.EmailField(_("Email address"), blank=True, null=True)
    phone = models.CharField(_("Phone number"),max_length=15, blank=True)
    addr1 = models.CharField(verbose_name=_('Address (line 1)'),max_length=200,
                                    help_text=_('The street and number of the customer'),blank=True,null=True)
    addr2 = models.CharField(verbose_name=_('Address (line 2)'),max_length=200,
                                    help_text=_('The town and country of the customer'),blank=True,null=True)
    zip = models.CharField(_("Zip code"),max_length=5, blank=True,null=True)
    cif = models.CharField(_("Tax number"),max_length=15, unique=True)
    saves_paper = models.BooleanField(
        _("Electronic receipt"),
        default=False,
        help_text=_("Desires to receive the receipts electronically"),
    )
    profile = models.ForeignKey(CustomerProfile,blank=True,null=True,on_delete=models.SET_NULL,related_name='customers')
    credit = models.FloatField(verbose_name=_("Accumulated credit"),help_text=_("Currently accumulated credit"),
                                     default=0.0, blank=True)
    
    def clean(self):
        from django.core.exceptions import ValidationError  
        if self.saves_paper and not self.email:
            raise ValidationError({'email':(_('An email is required if electronic receipt is used'))})
        
    def __str__(self):
        if self.first_name and self.last_name:
            value= self.first_name+" "+self.last_name[0]+"."
        elif self.email:
            value= self.email
        else:
            value= _("Customer ") + str(self.id)
            
        if self.canExchangeCredit:
            value +=' (' + str(round(self.credit,2))+"€)"
        return value
    
    def addCredit(self,amount):
        self.credit = round(self.credit+amount,2)
        self.save(update_fields=("credit",))

    def setCredit(self,value):
        self.credit = round(value,2)
        self.save(update_fields=("credit",))

    def toJSON(self):
        return {'name':self.first_name,'surname':self.last_name,'email':self.email,'cif':self.cif,'addr1':self.addr1,'addr2':self.addr2,'zip':self.zip}

    @property
    def canExchangeCredit(self,):
        from myTPV.models import SiteSettings
        SETTINGS=SiteSettings.load()
        if SETTINGS.ACCUMULATION:
            if self.credit and self.credit >= SETTINGS.MIN_ACCUM:
                return True
        return False
            
    @property
    def hasDiscount(self,):
        return self.profile and self.profile.percent>0

    @staticmethod
    def find(data):
        customer=None
        try:
            customer = Customer.objects.get(phone=data)
            return customer
        except:
            pass
        try:
            customer = Customer.objects.get(email=data.lower())
            return customer
        except:
            pass
        try:
            customer = Customer.objects.get(cif=data.upper())
            return customer
        except:
            pass
        return customer

class User(AbstractBaseUser,PermissionsMixin):
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

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
                    

