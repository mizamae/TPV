from django.db import models
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
User=get_user_model()
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.core.cache import cache
from django.contrib import admin
from django.utils import timezone
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
import base64
from .tasks import publish_familyUpdates, publish_familyDelete, publish_productUpdates, publish_productDelete, send_email, sendBillReceipt

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
    short_description = models.CharField(_("Brief description"), max_length=300)
    long_description = models.CharField(_("Detailed description"), max_length=1000)

    class Meta:
        ordering = ['name']
   
    def __str__(self) -> str:
        return self.name
    
    def serialize(self,update_fields=None):
        data={}
        data['id']=self.id

        if update_fields is None:
            update_fields=['picture','name','short_description','long_description']

        for field in update_fields:
            if field != 'picture':
                data[field]=getattr(self, field)
        
        if 'picture' in update_fields:
            if os.path.isfile(self.picture.path):
                with open(self.picture.path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read())

                data['image'] = str(encoded_string)[2:] # this is to remove the 'b/ header'
                _, extension = os.path.splitext(self.picture.name)
                data['image_extension'] = extension
            else:
                data['image'] = None
        return data
    
    @admin.display(description=_("Number of products"))
    def getNumberOfProducts(self,):
        return Product.objects.filter(family=self).count()
        
    def clean_name(self):
        self.name=self.name.strip().upper()

@receiver(post_save, sender=ProductFamily, dispatch_uid="update_ProductFamily_onSave")
def update_ProductFamily_onSave(sender, instance, created, **kwargs):
    publish_familyUpdates.delay(family_id=instance.id,update_fields=None)

@receiver(post_delete, sender=ProductFamily, dispatch_uid="updateProductFamily_onDelete")
def updateProductFamily_onDelete(sender, instance, **kwargs):
    publish_familyDelete.delay(id=instance.id)

class Manufacturer(models.Model):
    class Meta:
        verbose_name = _('Manufacturer')
        verbose_name_plural = _('Manufacturers')

    name = models.CharField(max_length=50, unique=True,verbose_name=_("Name"))
    
    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name
    
    @admin.display(description=_("Number of products"))
    def getNumberOfProducts(self,):
        return self.consumibles.count()
        
    def clean_name(self):
        self.name=self.name.strip().upper()

class Consumible(models.Model):
    class Meta:
        verbose_name = _('Consumable')
        verbose_name_plural = _('Consumables')
        unique_together=(('name','manufacturer'))

    picture = models.ImageField(_('Image'),null=True,blank=True,storage=IMAGES_FILESYSTEM)
    name = models.CharField(max_length=150, verbose_name=_("Name"))

    barcode = models.CharField(max_length=150, unique=True,verbose_name=_("Barcode"),blank=True,null=True)

    comments = models.TextField(_('Comments'),blank=True,null=True)
    family = models.ForeignKey(ProductFamily,verbose_name=_("Family"), on_delete=models.CASCADE, related_name='consumibles')
    manufacturer = models.ForeignKey(Manufacturer,verbose_name=_("Manufacturer"), on_delete=models.CASCADE, related_name='consumibles')

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
            self.updateCache()
    
    def increment_stock(self,quantity):
        if not self.infinite:
            self.stock += quantity
            self.save(update_fields=['stock',])
            self.updateCache()
    
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

    def updateCache(self):
        cached = cache.get("consumable_info")
        if type(cached) is dict:
            cached[self.id]={'stock': self.stock}
            cache.set("consumable_info",cached,None)
        for product in self.getProductsWhereUsed()['products']:
            product.updateCache()

@receiver(post_save, sender=Consumible, dispatch_uid="create_Product_onCreate")
def create_Product_onCreate(sender, instance, created, **kwargs):
    if created and instance.generates_product:
        product = Product.objects.create(picture=instance.picture,name=instance.name,barcode=instance.barcode,
                            family=instance.family,single_ingredient=True,vat=instance.vat,details = instance.comments) 
        CombinationPosition.objects.get_or_create(product=product,quantity=1,ingredient=instance)
    instance.updateCache()

class Product(models.Model):
    class Meta:
        verbose_name = _('Sellable product')
        verbose_name_plural = _('Sellable products')

    picture = models.ImageField(verbose_name=_('Image of the product'),null=True,blank=True,storage=IMAGES_FILESYSTEM)
    barcode = models.CharField(max_length=150, unique=True,verbose_name=_("Barcode"))
    name = models.CharField(max_length=150, verbose_name=_("Name of the product"))
    details = models.TextField(_('Details'),blank=True,null=True)
    family = models.ForeignKey(ProductFamily, on_delete=models.CASCADE, related_name='products')    

    single_ingredient = models.BooleanField(verbose_name=_("Direct from consumable"),default=False)
    ingredients = models.ManyToManyField(Consumible,blank=True,through='CombinationPosition')

    manual_price = models.FloatField(verbose_name=_("Override selling price"),help_text=_("Override automatic selling price of one unit"),blank=True,null=True)

    discount = models.ForeignKey('ProductDiscount', on_delete=models.SET_NULL, related_name='products',blank=True,null=True)
    promotion = models.ForeignKey('ProductPromotion', on_delete=models.SET_NULL, related_name='products',blank=True,null=True)

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
    
    def serialize(self,update_fields=None):
        default_serialize_fields = ['name','picture','details','family','discount','promotion','pvp','stock']
        data={}
        data['id']=self.id
        
        if update_fields is None:
            update_fields=default_serialize_fields
        else:
            for field in update_fields:
                if not field in default_serialize_fields:
                    update_fields.remove(field)
            update_fields += ['pvp','stock']

        for field in update_fields:
            data[field]=getattr(self, field)
            if field in ['family',]:
                data[field] = data[field].id
            elif field in ['discount','promotion']:
                data[field] = str(data[field])
        
        if 'picture' in update_fields:
            del data['picture']
            if self.picture and os.path.isfile(self.picture.path):
                with open(self.picture.path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read())

                data['image'] = str(encoded_string)[2:] # this is to remove the 'b/ header'
                _, extension = os.path.splitext(self.picture.name)
                data['image_extension'] = extension
            else:
                data['image'] = None
        return data

    def getVATValue(self):
        if self.vat:
            return self.vat.pc_value
        else: # gets the standard value
            return cache.get("DefaultVAT")
    
    def getVATAmount(self):
        return round(self.price*self.getVATValue()/100,2)

    @property
    def manufacturer(self):
        return self.Ingredients.first().manufacturer if self.single_ingredient else None

    @property
    def Ingredients(self):
        return CombinationPosition.objects.filter(product=self)
    
    @property
    @admin.display(description=_("Cost"))
    def cost(self,):
        cost=0
        for comp in self.Ingredients:
            cost+=comp.quantity*comp.ingredient.cost
        return round(cost,2)
    
    @property
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
        cached = cache.get("products_info")
        if type(cached) is dict:
            try:
                value = round(cached[self.id]['pvp'],2)
            except:
                self.updateCache()
                cached = cache.get("products_info")  
                value = round(cached[self.id]['pvp'],2)
        else:
            value = self.pvpFromDB
        return value
    
    @property
    def pvpFromDB(self,):
        return round(self.price+self.getVATAmount(),2)
    
    @property
    def stock(self):
        cached = cache.get("products_info")
        if type(cached) is dict:
            try:
                value = cached[self.id]['stock']
            except:
                self.updateCache()      
                cached = cache.get("products_info")  
                value = cached[self.id]['stock']
        else:
            value = self.stockFromDB
        return value
        
    @property
    def stockFromDB(self):
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
    
    def updateCache(self):
        cached = cache.get("products_info")
        if type(cached) is dict:
            cached[self.id]={'pvp':self.pvpFromDB,'stock':self.stockFromDB}
            cache.set("products_info",cached,None)

@receiver(post_save, sender=Product, dispatch_uid="updateProductsCache")
def updateProductsCache(sender, instance, **kwargs):
    instance.updateCache()
    update_fields=kwargs.get('update_fields',None)
    if update_fields:
        update_fields = list(update_fields)
    publish_productUpdates.delay(product_id=instance.id,update_fields=update_fields)

@receiver(post_delete, sender=Product, dispatch_uid="updateProducts_onDelete")
def updateProducts_onDelete(sender, instance, **kwargs):
    publish_productDelete.delay(product_id=instance.id)

class ProductPromotion(models.Model):
    units_pay = models.SmallIntegerField(verbose_name=_("Units to pay"))
    units_take = models.SmallIntegerField(verbose_name=_("Units to take"))

    @admin.display(description=_("Description"))
    def __str__(self):
        return str(self.units_take) +"x"+ str(self.units_pay)
    
    def clean(self,):
        from django.core.exceptions import ValidationError  
        if self.units_pay >= self.units_take:
            raise ValidationError({'units_take':(_('The units taken by customer should be greater than the units paid to be a promotion'))})
    
    @admin.display(description=_("Affected products"))
    def adminAffectedProducts(self,):
        return list(map(str,self.affectedProducts))
    
    @property
    def affectedProducts(self):
        return self.products.all()
    
    def getEffectiveQuantity(self,quantity):
        if quantity >= self.units_take:
            return quantity - quantity // self.units_take
        else:
            return quantity

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
        return self.products.all()

class CombinationPosition(models.Model):
    class Meta:
        verbose_name = _('Combination of consumables')
        verbose_name_plural = _('Combinations of consumables')

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='resultant_product')
    quantity = models.FloatField(default=1,verbose_name=_("Quantity"))
    ingredient = models.ForeignKey(Consumible, on_delete=models.CASCADE, related_name='isUsedIn',verbose_name=_("Consumable"))

    def __str__(self) -> str:
        return str(self.ingredient)

@receiver(post_save, sender=CombinationPosition, dispatch_uid="updateCompoundProductsCache")
def updateCompoundProductsCache(sender, instance, **kwargs):
    instance.product.updateCache()

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
    PAYMENTTYPE_BIZUM=2

    PAYMENT_TYPES = (
        (PAYMENTTYPE_CASH, _("On cash")),
        (PAYMENTTYPE_CREDITCARD, _("By credit card")),  
        (PAYMENTTYPE_BIZUM, _("By Bizum")),        
    )

    code = models.CharField(max_length=20,editable=False)
    owner = models.ForeignKey(settings.CUSTOMER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='owner',editable = True)
    createdBy = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='createdBy',editable = False)
    createdOn = models.DateTimeField(verbose_name=_("Date and time"),auto_now_add=True)

    status = models.PositiveSmallIntegerField(verbose_name=_("Status"),default=STATUS_OPEN,editable = True,choices=STATUS_TYPES)

    positions = models.ManyToManyField(Product,blank=True,through='BillPosition',related_name="bill_lines")

    paymenttype = models.PositiveSmallIntegerField(verbose_name=_("Payment"),blank=False,null=True,choices=PAYMENT_TYPES)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self.code + _(" of customer ")+ str(self.owner)
    
    def save(self,*args,**kwargs):            
        super(BillAccount,self).save(*args,**kwargs)
    
    def add_bill_position(self,product,quantity=1):
        position,created=BillPosition.objects.get_or_create(bill=self,product=product)
        if created:
            position.update(quantity)
            position.product.reduce_stock(quantity=quantity)
        else:
            position.set_quantity(quantity=position.quantity+quantity)
        return position

    def close(self):
        if self.paymenttype is not None:
            # self.total = self.getTotalBeforeVAT()
            # self.vat_amount = self.getVATAmount()
            # self.save_amount = self.getSaveAmount()
            self.status = BillAccount.STATUS_PAID
            self.save(update_fields=['status',]) #'vat_amount','total','save_amount'])
            for position in self.bill_positions.all():
                position.close()
            if self.owner and self.owner.saves_paper:
                sendBillReceipt.delay(billData=self.toJSON())

    def setOwner(self,customer):
        self.owner = customer
        self.save(update_fields=['owner',])

    def toJSON(self):
        value = {'code':self.code,'customer':self.owner.toJSON() if self.owner else {},
                 'date':self.createdOn,'status':self.status,'total':self.total,"vat":self.getVATAmount(),'positions':[]}
        for position in self.bill_positions.all():
            value['positions'].append({'quantity':position.quantity,'product':str(position.product),
                                       'vat_amount':position.getVATAmount(),'subtotal':position.getSubtotal(),'reduce_concept':position.reduce_concept})
        return value

    @property
    @admin.display(description=_("Total including VAT and discounts"))
    def total(self,):
        total=0
        for position in self.bill_positions.all():
            total+=position.getSubtotal()
        return round(total,2)
    
    @admin.display(description=_("VAT amount"))
    def getVATAmount(self,):
        total=0
        for position in self.bill_positions.all():
            total+=position.getVATAmount()
        return round(total,2)
        
    @staticmethod
    def create(createdBy):
        instance = BillAccount()
        instance.createdBy = createdBy
        date = timezone.now().replace(microsecond=0)
        instance.createdOn = date
        number = BillAccount.objects.filter(createdOn__date__year = date.year).count()
        instance.code = str(date.year) + "-" + str(number+1)
        instance.save()
        return instance

@receiver(pre_delete, sender=BillAccount, dispatch_uid="restoreStock_onDelete")
def restoreStock_onDelete(sender, instance, **kwargs):
    for position in instance.bill_positions.all():
        position.reduce_quantity(quantity=position.quantity)


class BillPosition(models.Model):
    position = models.SmallIntegerField(verbose_name=_("Position"),null=True,blank=True,editable = True)
    bill = models.ForeignKey(BillAccount, on_delete=models.CASCADE, related_name='bill_positions')
    quantity = models.PositiveSmallIntegerField(default=1,verbose_name=_("Quantity"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bill_positions')
    
    subtotal = models.FloatField(verbose_name=_("Subtotal"),help_text=_("Selling price at the moment of the operation"),blank=True,null=True)
    vat_amount = models.FloatField(verbose_name=_("VAT amount"),help_text=_("VAT amount at the moment of the operation"),blank=True,null=True)

    reduce_concept = models.CharField(max_length=20,editable=False,blank=True,null=True)

    class Meta:
        unique_together = ['bill','product']
    
    def __str__(self) -> str:
        return str(self.product)
    
    def save(self, *args, **kwargs):
        if self.id is None:
            self.position = self.getNextPosition()
        return super(BillPosition, self).save(*args, **kwargs)
    
    def close(self,):
        self.subtotal = self.getSubtotal()
        self.vat_amount = self.getVATAmount()
        self.save(update_fields=['subtotal','vat_amount'])

    def set_quantity(self,quantity):
        if quantity > self.quantity:
            self.product.reduce_stock(quantity=quantity-self.quantity)
        else:
            self.product.increase_stock(quantity=self.quantity-quantity)
        self.update(quantity=quantity)

    def increase_quantity(self,quantity):
        self.product.reduce_stock(quantity=quantity)
        self.update(quantity=self.quantity+quantity)
        
    def reduce_quantity(self, quantity):
        self.product.increase_stock(quantity=quantity)
        self.update(quantity=self.quantity-quantity)

    def update(self, quantity):
        if quantity > 0 :
            if self.product.discount:
                self.reduce_concept =  "-" + str(self.product.discount)
            else:
                self.reduce_concept = None
            self.quantity=quantity

            if self.product.promotion:
                if self.product.promotion.getEffectiveQuantity(quantity = self.quantity) != self.quantity:
                    text = str(self.product.promotion)
                else:
                    text=""
                if self.reduce_concept:
                    if text:
                        if not text in self.reduce_concept:
                            self.reduce_concept += " " + text
                    else:
                        self.reduce_concept = self.reduce_concept.replace(str(self.product.promotion),"")
                else:
                    self.reduce_concept = text

            self.save(update_fields=['quantity','reduce_concept'])
        else:
            self.delete()
    
    def getNextPosition(self):
        return BillPosition.objects.filter(bill=self.bill).count()+1
    
    def getVATAmount(self):
        if self.vat_amount:
            return self.vat_amount
        else:
            if self.product.promotion:
                promotion_quantity = self.product.promotion.getEffectiveQuantity(quantity = self.quantity)
                return round(promotion_quantity*self.product.getVATAmount(),2)
            return round(self.quantity*self.product.getVATAmount(),2)
        
    def getSubtotal(self):
        if self.subtotal:
            return self.subtotal
        else:
            if self.product.promotion:
                promotion_quantity = self.product.promotion.getEffectiveQuantity(quantity = self.quantity)
                return round(promotion_quantity*self.product.pvp,2)
            return round(self.quantity*self.product.pvp,2)
    
    def getUnitPVP(self):
        return round(self.getSubtotal()/self.quantity,2)