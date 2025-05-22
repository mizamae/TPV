from django.db import models
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
User=get_user_model()
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib import admin
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
from .tasks import send_email, sendBillReceipt

import os
FILE_DIR = os.path.join(settings.MEDIA_ROOT)
IMAGES_FILESYSTEM = FileSystemStorage(location=FILE_DIR,base_url=settings.MEDIA_URL)

# Create your models here.

class VATValue(models.Model):
    class Meta:
        verbose_name = _('VAT value')
        verbose_name_plural = _('VAT values')

    name = models.CharField(max_length=30, unique=True,verbose_name=_("Name"))
    pc_value = models.FloatField(verbose_name=_("Percentage value"),help_text=_("Percentage over product value"))

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name + " ("+str(self.pc_value)+"%)"

class ProductFamily(models.Model):
    class Meta:
        verbose_name = _('Product family')
        verbose_name_plural = _('Product families')

    picture = models.ImageField(_('Image'),null=True,blank=True,storage=IMAGES_FILESYSTEM)
    name = models.CharField(max_length=30, unique=True,verbose_name=_("Name"))
    
    class Meta:
        ordering = ['name']
   
    def __str__(self) -> str:
        return self.name
    
    @admin.display(description=_("Number of products"))
    def getNumberOfProducts(self,):
        return Product.objects.filter(family=self).count()
        
    def clean_name(self):
        self.name=self.name.strip().upper()

class Consumible(models.Model):
    class Meta:
        verbose_name = _('Consumable')
        verbose_name_plural = _('Consumables')

    picture = models.ImageField(_('Image'),null=True,blank=True,storage=IMAGES_FILESYSTEM)
    name = models.CharField(max_length=150, unique=True,verbose_name=_("Name"))
    barcode = models.CharField(max_length=150, unique=True,verbose_name=_("Barcode"),blank=True,null=True)

    comments = models.TextField(_('Comments'),blank=True,null=True)
    family = models.ForeignKey(ProductFamily,verbose_name=_("Family"), on_delete=models.CASCADE, related_name='consumible_family')
    cost = models.FloatField(verbose_name=_("Unitary cost"),help_text=_("Cost of one unit excluding VAT"))
    price = models.FloatField(verbose_name=_("Selling price"),help_text=_("Selling price of one unit excluding VAT"))
    order_quantity = models.FloatField(verbose_name=_("Minimum order quantity"),default=10,
                                             help_text=_("Determines the minimum quantity that can be sourced from supplier"))
    stock = models.FloatField(verbose_name=_("Current stock"),blank=True,default=0,
                                             help_text=_("Quantity in stock currently"))
    stock_min = models.FloatField(verbose_name=_("Minimum stock"),blank=True,default=0,
                                                 help_text=_("Quantity in stock that will require a new purchase order"))
    generates_product = models.BooleanField(verbose_name=_("Can be directly sold"),default=False)
    infinite = models.BooleanField(verbose_name=_("Infinite consumable"),default=False)
    
    vat = models.ForeignKey(VATValue,verbose_name=_("Applicable VAT"), on_delete=models.SET_NULL, related_name='consumibles', null=True)

    def __str__(self) -> str:
        return self.name
    
    def clean(self):
        from django.core.exceptions import ValidationError  
        if self.generates_product and not self.barcode:
            raise ValidationError({'barcode':(_('A barcode is required if consumable is to be sold directly'))})

    def reduce_stock(self,quantity):
        if not self.infinite:
            self.stock -= quantity
            self.stock = round(self.stock,2)
            if self.stock <= self.stock_min:
                recipients=User.getStaffEmails()
                if recipients!=[]:
                    send_email.delay(
                            subject=_('[STOCK_WARNING] Product below the minimum stock level'),
                            message=_('The consumable ' + str(self)+' has reached an stock level below its minimum.\n Now its stock is '+str(self.stock)),
                            recipient_list=recipients)
                
            self.save(update_fields=['stock',])
    
    def increment_stock(self,quantity):
        if not self.infinite:
            self.stock += quantity
            self.save(update_fields=['stock',])
    
    def getProductsWhereUsed(self):
        positions= CombinationPosition.objects.filter(ingredient=self)
        products=[]
        quantities={}
        for pos in positions:
            products.append(pos.product)
            quantities[pos.product.id]=pos.quantity
        return {'products':products,'quantities':quantities}
    
    def get_monthly_consumption(self,month,year):
        consumption=0
        info = self.getProductsWhereUsed()
        startDate = datetime.date(year=year,month=month,day=1)
        if month<=11:
            endDate = datetime.date(year=year,month=month+1,day=1)
        else:
            endDate = datetime.date(year=year+1,month=1,day=1)
        
        positions = BillPosition.objects.filter(bill__createdOn__gte=startDate,bill__createdOn__lte=endDate,product__in=info['products'])
        for pos in positions:
            factor = info['quantities'][pos.product.id]
            consumption+=pos.quantity*factor
        return round(consumption,2)
    
    @staticmethod
    def get_stock_value():
        cons = Consumible.objects.filter(infinite=False)
        value=0
        for con in cons:
            value+=con.stock*con.cost
        return round(value,2)

    @staticmethod
    def get_monthly_cost(month,year):
        cost=0
        consumibles = Consumible.objects.all()
        for cons in consumibles:
            cost += cons.get_monthly_consumption(month=month,year=year)*cons.cost
        return cost
    
    @staticmethod
    def get_monthly_ingress(month,year):
        ingress=0
        consumibles = Consumible.objects.all()
        for cons in consumibles:
            ingress += cons.get_monthly_consumption(month=month,year=year)*cons.price
        return ingress

@receiver(post_save, sender=Consumible, dispatch_uid="create_Product_onCreate")
def create_Product_onCreate(sender, instance, created, **kwargs):
    if created and instance.generates_product:
        product = Product.objects.create(picture=instance.picture,name=instance.name,barcode=instance.barcode,
                            family=instance.family,single_ingredient=True,vat=instance.vat) 
        CombinationPosition.objects.get_or_create(product=product,quantity=1,ingredient=instance)

class Product(models.Model):
    class Meta:
        verbose_name = _('Sellable product')
        verbose_name_plural = _('Sellable products')

    picture = models.ImageField(verbose_name=_('Image of the product'),null=True,blank=True,storage=IMAGES_FILESYSTEM)
    barcode = models.CharField(max_length=150, unique=True,verbose_name=_("Barcode"))
    name = models.CharField(max_length=150, unique=True,verbose_name=_("Name of the product"))
    details = models.TextField(_('Details'),blank=True,null=True)
    family = models.ForeignKey(ProductFamily, on_delete=models.CASCADE, related_name='family')    

    single_ingredient = models.BooleanField(verbose_name=_("Direct from consumable"),default=False)
    ingredients = models.ManyToManyField(Consumible,blank=True,through='CombinationPosition')

    manual_price = models.FloatField(verbose_name=_("Override selling price"),help_text=_("Override automatic selling price of one unit"),blank=True,null=True)

    discount = models.ForeignKey('ProductDiscount', on_delete=models.SET_NULL, related_name='products_affected',blank=True,null=True)

    vat = models.ForeignKey(VATValue,verbose_name=_("Applicable VAT"), on_delete=models.SET_NULL, related_name='products',null=True)

    class Meta:
        ordering = ['name']
    
    def save(self, **kwargs):
        self.name=self.name.strip().upper()
        if self.manual_price and self.manual_price <=0:
            self.manual_price=None
        return super().save(**kwargs)
        
    def __str__(self) -> str:
        return self.name
    
    def getVATValue(self):
        if self.vat:
            return self.vat.pc_value
        else: # gets the standard value
            return VATValue.objects.get(id=1).pc_value
    
    def getVATAmount(self):
        return round(self.price()*self.getVATValue()/100,2)

    @property
    def Ingredients(self):
        return CombinationPosition.objects.filter(product=self)
    
    @admin.display(description=_("Cost"))
    def cost(self,):
        cost=0
        for comp in self.Ingredients:
            cost+=comp.quantity*comp.ingredient.cost
        return round(cost,2)
    
    @admin.display(description=_("Sell price"))
    def price(self,):
        if self.discount:
            factor = (100-self.discount.percent)/100
        else:
            factor = 1

        if self.manual_price:
            return round(factor*self.manual_price,2)
        else:
            price=0
            for comp in self.Ingredients:
                price+=comp.quantity*comp.ingredient.price
            return round(factor*price,2)
        
    @property
    def pvp(self):
        if self.discount:
            factor = (100-self.discount.percent)/100
        else:
            factor = 1

        vat = self.getVATValue()/100

        if self.manual_price:
            return round((1+vat)*factor*self.manual_price,2)
        else:
            pvp=0
            for comp in self.Ingredients:
                pvp+=comp.quantity*comp.ingredient.price
            return round((1+vat)*factor*pvp,2) 
    
    @property
    def stock(self):
        stock_value = 1e6
        for comp in self.Ingredients:
            stock_value = min(stock_value,comp.ingredient.stock/comp.quantity)
        return round(stock_value)

    def reduce_stock(self,quantity):
        for comp in self.Ingredients:
            comp.ingredient.reduce_stock(quantity = quantity*comp.quantity )    
    
    def increase_stock(self,quantity):
        for comp in self.Ingredients:
            comp.ingredient.increment_stock(quantity = quantity*comp.quantity )


class ProductDiscount(models.Model):
    PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]

    percent = models.FloatField(default=0,verbose_name=_("Percentage over selling price"),validators=PERCENTAGE_VALIDATOR)

    def __str__(self):
        return str(round(self.percent,1))+"%"
    
    @admin.display(description=_("Affected products"))
    def adminAffectedProducts(self,):
        return list(map(str,self.affectedProducts))
    
    @property
    def affectedProducts(self):
        return self.products_affected.all()

class CombinationPosition(models.Model):
    class Meta:
        verbose_name = _('Combination of consumables')
        verbose_name_plural = _('Combinations of consumables')

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='resultant_product')
    quantity = models.FloatField(default=1,verbose_name=_("Quantity"))
    ingredient = models.ForeignKey(Consumible, on_delete=models.CASCADE, related_name='ingredient',verbose_name=_("Consumable"))

    def __str__(self) -> str:
        return str(self.ingredient)

class BillAccount(models.Model):

    STATUS_OPEN=0
    STATUS_CLOSED=1
    STATUS_PAID=2
    STATUS_TYPES = (
        (STATUS_OPEN, _("Open")),
        (STATUS_CLOSED, _("Closed not Paid")),
        (STATUS_PAID, _("Closed and Paid")),        
    )

    PAYMENTTYPE_CASH=0
    PAYMENTTYPE_CREDITCARD=1

    PAYMENT_TYPES = (
        (PAYMENTTYPE_CASH, _("On cash")),
        (PAYMENTTYPE_CREDITCARD, _("By credit card")),        
    )

    code = models.CharField(max_length=20,editable=False)
    owner = models.ForeignKey(settings.CUSTOMER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='owner',editable = True)
    createdBy = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='createdBy',editable = False)
    createdOn = models.DateTimeField(verbose_name=_("Date and time"),auto_now_add=True)

    status = models.PositiveSmallIntegerField(verbose_name=_("Status"),default=STATUS_OPEN,editable = True,choices=STATUS_TYPES)

    positions = models.ManyToManyField(Product,blank=True,through='BillPosition',related_name="bill_lines")

    paymenttype = models.PositiveSmallIntegerField(verbose_name=_("Payment"),blank=False,null=True,choices=PAYMENT_TYPES)

    total = models.FloatField(verbose_name=_("Total amount"),help_text=_("Total cost of the invoice before VAT"),blank=True,null=True)
    vat_amount = models.FloatField(verbose_name=_("VAT amount"),help_text=_("Total amount of the VAT"),blank=True,null=True)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self.code + _(" of customer ")+ str(self.owner)
    
    def save(self,*args,**kwargs):
        create = self.id is None
        if create:
            date = timezone.now()
            number = BillAccount.objects.filter(createdOn__date__year = date.year).count()
            self.code = str(date.year) + "-" + str(number+1)
        super(BillAccount,self).save(*args,**kwargs)
    
    # def bill_positions(self):
    #     return BillPosition.objects.filter(bill=self).order_by("product__name")
    
    def add_bill_position(self,product,quantity=1):
        instance,created=BillPosition.objects.get_or_create(bill=self,product=product)
        if created:
            instance.quantity=quantity
        else:
            instance.quantity+=quantity
        product.reduce_stock(quantity=quantity)
        instance.save()
        return instance

    def close(self):
        if self.paymenttype is not None:
            self.total = self.getTotalBeforeVAT()
            self.vat_amount = self.getVATAmount()
            self.status = BillAccount.STATUS_PAID
            self.save(update_fields=['status','vat_amount','total'])
            for position in self.bill_positions.all():
                position.close()
            if self.owner and self.owner.saves_paper:
                sendBillReceipt.delay(billData=self.toJSON())

    def setOwner(self,customer):
        self.owner = customer
        self.save(update_fields=['owner',])

    def toJSON(self):
        value = {'code':self.code,'customer':self.owner.toJSON() if self.owner else {},
                 'date':self.createdOn,'status':self.status,'total':self.getTotalBeforeVAT(),"vat":self.getVATAmount(),'positions':[]}
        for position in self.bill_positions.all():
            value['positions'].append({'quantity':position.quantity,'product':str(position.product),
                                       'pvp':position.pvp,'subtotal':position.quantity*position.pvp})
        return value

    @admin.display(description=_("Total including VAT"))
    def getTotal(self,):
        if self.status!=BillAccount.STATUS_PAID:
            return round(self.getTotalBeforeVAT()+self.getVATAmount(),2)
        else:
            return round(self.total+self.vat_amount,2)
    
    @admin.display(description=_("Total before VAT"))
    def getTotalBeforeVAT(self,):
        total=0
        for position in self.bill_positions.all():
            total+=position.quantity*position.product.price()
        return round(total,2)
    
    @admin.display(description=_("VAT amount"))
    def getVATAmount(self,):
        total=0
        for position in self.bill_positions.all():
            total+=position.quantity*(position.product.getVATAmount())
        return round(total,2)
    
    @staticmethod
    def create(createdBy):
        instance = BillAccount()
        instance.createdBy = createdBy
        instance.save()
        return instance
        
class BillPosition(models.Model):
    position = models.SmallIntegerField(verbose_name=_("Position"),null=True,blank=True,editable = True)
    bill = models.ForeignKey(BillAccount, on_delete=models.CASCADE, related_name='bill_positions')
    quantity = models.PositiveSmallIntegerField(default=1,verbose_name=_("Quantity"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bill_positions')
    pvp = models.FloatField(verbose_name=_("Selling price"),help_text=_("Selling price at the moment of the operation"),blank=True,null=True)

    class Meta:
        unique_together = ['bill','product']
    
    def __str__(self) -> str:
        return str(self.product)
    
    def save(self, *args, **kwargs):
        if self.id is None:
            self.position = self.getNextPosition()
        return super(BillPosition, self).save(*args, **kwargs)
    
    def close(self,):
        self.pvp = self.product.pvp
        self.save(update_fields=['pvp',])

    def set_quantity(self,quantity):
        if quantity > self.quantity:
            self.product.reduce_stock(quantity=quantity-self.quantity)
        else:
            self.product.increase_stock(quantity=self.quantity-quantity)
        self.update(quantity=quantity)

    def increase_quantity(self,quantity):
        self.update(quantity=self.quantity+quantity)
        self.product.reduce_stock(quantity=quantity)
    
    def reduce_quantity(self, quantity):
        self.update(quantity=self.quantity-quantity)
        self.product.increase_stock(quantity=quantity)

    def update(self, quantity):
        if quantity > 0 :
            self.quantity=quantity
            self.save(update_fields=['quantity',])
        else:
            self.delete()
    
    def getNextPosition(self):
        return BillPosition.objects.filter(bill=self.bill).count()+1
    
    def getsubtotal(self):
        if self.pvp:
            return round(self.quantity * self.pvp,2)
        else:
            return round(self.quantity * self.product.pvp,2)