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
from .tasks import publish_familyUpdates, publish_familyDelete, publish_productUpdates, publish_productDelete, send_email, sendBillReceipt, printBillReceipt

from PIL import Image, ExifTags
import uuid
import os
FILE_DIR = os.path.join(settings.MEDIA_ROOT)
IMAGES_FILESYSTEM = FileSystemStorage(location=FILE_DIR,base_url=settings.MEDIA_URL)

# Create your models here.

class VATValue(models.Model):
    class Meta:
        verbose_name = _('VAT value')
        verbose_name_plural = _('VAT values')

    name = models.CharField(max_length=30, unique=True,verbose_name=_("Name"))
    pc_value = models.FloatField(verbose_name=_("Percentage value"),
                                 help_text=_("Percentage over product value"))

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name + " ("+str(self.pc_value)+"%)"

class ModelWithImage:

    # Method for image compression
    def compress_image(self, source_field, target_field, size):
        if not getattr(self, source_field):
            # If the source_field is empty, no need to proceed
            return
        # Open the original image
        img = Image.open(getattr(self, source_field))
        # Check for EXIF orientation and rotate if necessary
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                try:
                    exif = dict(img._getexif().items())
                    if exif[orientation] == 3:
                        img = img.rotate(180, expand=True)
                    elif exif[orientation] == 6:
                        img = img.rotate(270, expand=True)
                    elif exif[orientation] == 8:
                        img = img.rotate(90, expand=True)
                except (AttributeError, KeyError, IndexError):
                    # No EXIF data or invalid data, don't perform rotation
                    pass
        # Calculate the aspect ratio to maintain proportions when resizing
        aspect_ratio = img.width / img.height
        # Resize the image to the specified size
        img = img.resize((size, int(size / aspect_ratio)))
        # Convert the image to RGB mode if it's in RGBA mode
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        # Save the compressed image to the target_field's upload_to path inside MEDIA_ROOT
        target_upload_to = getattr(self.__class__, target_field).field.upload_to

        img_path = getattr(self, source_field).path
        img_name, img_ext = os.path.splitext(os.path.basename(img_path))
        unique_id = str(uuid.uuid4())
        compressed_img_name = f'{img_name}{unique_id}_{size}{img_ext}'
        compressed_img_path = os.path.join(settings.MEDIA_ROOT, target_upload_to, compressed_img_name)
        # Ensure that the target directory exists before saving
        os.makedirs(os.path.dirname(compressed_img_path), exist_ok=True)
        # Save the image as JPEG
        img.save(compressed_img_path, 'JPEG')
        img.close()
        #os.remove(getattr(self, source_field).path)
        # Set the target_field with the compressed image path relative to MEDIA_ROOT
        setattr(self, target_field, os.path.relpath(compressed_img_path, settings.MEDIA_ROOT))

class ProductFamily(models.Model,ModelWithImage):
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
    
    def save(self, *args, **kwargs):
        if self.picture:
            self.compress_image(source_field='picture', target_field='picture', size=200)
        super(ProductFamily, self).save(*args, **kwargs)

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

class Consumible(models.Model,ModelWithImage):
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
    generates_product = models.BooleanField(verbose_name=_("Can be directly sold"),default=True)
    infinite = models.BooleanField(verbose_name=_("Infinite consumable"),default=False)
    
    vat = models.ForeignKey(VATValue,verbose_name=_("Applicable VAT"), on_delete=models.SET_NULL, related_name='consumibles', null=True)

    def __str__(self) -> str:
        return self.name
    
    def save(self, *args, **kwargs):
        if self.picture:
            self.compress_image(source_field='picture', target_field='picture', size=200)
        super(Consumible, self).save(*args, **kwargs)

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

class Product(models.Model,ModelWithImage):
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

    credit_acc_factor = models.FloatField(verbose_name=_("Credit accumulation factor"),help_text=_("Factor of the price accumulated into customer's credit"),
                                          blank=True,null=True)

    class Meta:
        ordering = ['name']
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cached_picture_path = self.picture.path if self.picture else None

    def save(self, **kwargs):
        self.name=self.name.strip().upper()
        if self.manual_price and self.manual_price <=0:
            self.manual_price=None
        if self.picture:
            self.compress_image(source_field='picture', target_field='picture', size=200)
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
        if stock_value == 1e6:
            stock_value = 0
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
    if instance.picture and (instance.cached_picture_path != instance.picture.path):
        update_fields=['picture',]
    else:
        update_fields=[]
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

    number = models.PositiveSmallIntegerField(verbose_name=_("Number"),editable = True)
    
    status = models.PositiveSmallIntegerField(verbose_name=_("Status"),default=STATUS_OPEN,editable = True,choices=STATUS_TYPES)

    positions = models.ManyToManyField(Product,blank=True,through='BillPosition',related_name="bill_lines")

    userDiscount = models.FloatField(verbose_name=_("User discount"),help_text=_("Discount due to user affillation"),blank=True,null=True,editable = False)
    userCredit = models.FloatField(verbose_name=_("User credit"),help_text=_("Discount due to user credit"),blank=True,null=True,editable = False)

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
            
            if self.owner:
                if self.owner.saves_paper:
                    sendBillReceipt.delay(billData=self.toJSON())                    

                from myTPV.models import SiteSettings
                SETTINGS=SiteSettings.load()
                if SETTINGS.ACCUMULATION:
                    amount = 0
                    for position in self.bill_positions.all():
                        if position.credit_acc:
                            amount += position.credit_acc
                    self.owner.addCredit(amount)
            else:
                printBillReceipt.delay(billData=self.toJSON())

    def discountUserCredit(self):
        total = self.totalNoBillDiscounts-self.userDiscountAmount
        self.userCredit = self.owner.credit if self.owner.credit<total else total
        self.owner.addCredit(amount=-self.userCredit)
        self.save(update_fields=['userCredit',])

    def setOwner(self,customer):
        self.owner = customer
        if self.owner.hasDiscount:
            self.userDiscount=self.owner.profile.percent
        self.save(update_fields=['owner','userDiscount'])

    def toJSON(self):
        value = {'code':self.code,'customer':self.owner.toJSON() if self.owner else {},'paymentType':self.paymenttype,
                 'date':self.createdOn,'status':self.status,'total':self.total,"vat":self.getVATAmount(),'positions':[]}
        for position in self.bill_positions.all():
            if hasattr(position, "refund"):
                quantity = position.quantity-position.refund.quantity
            else:
                quantity = position.quantity
            if quantity>0:
                value['positions'].append({'quantity': quantity ,'product':str(position.product),
                                       'vat_amount':position.getVATAmount(),'subtotal':position.getSubtotal(),'reduce_concept':position.reduce_concept})
        if self.owner:
            if self.owner.hasDiscount:
                value['positions'].append({'quantity':1,'product':_("User discount"),
                                        'vat_amount':0,'subtotal':-self.userDiscountAmount,'reduce_concept':None})
            if self.userCredit:
                value['positions'].append({'quantity':1,'product':_("User credits"),
                                        'vat_amount':0,'subtotal':-self.userCredit,'reduce_concept':None})
        return value

    @property
    def refunds(self,):
        return Refund.objects.filter(bill_pos__in=self.bill_positions.all())
        
    @property
    def userDiscountAmount(self):
        if self.userDiscount:
            return round(self.totalNoBillDiscounts*(self.userDiscount/100.0),2)
        else:
            return 0
    
    @property
    def totalNoBillDiscounts(self,):
        total=0
        for position in self.bill_positions.all():
            total+=position.getSubtotal()
        return total

    @property
    @admin.display(description=_("Total including VAT and discounts"))
    def total(self,):
        total=self.totalNoBillDiscounts
        if self.userDiscount:
            total = total-self.userDiscountAmount
        if self.userCredit:
            total = total-self.userCredit
        
        return round(total,2)
    
    @property
    def totalRefunded(self,):
        total = 0
        for refund in self.refunds.all():
            total += refund.subtotal
        return round(total,2)
        
    @admin.display(description=_("VAT amount"))
    def getVATAmount(self,):
        ## TODO: discount the refunded amount of the VAT!!!
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
        previous = BillAccount.objects.filter(createdOn__date__year = date.year).order_by('-number').first()
        instance.number = previous.number+1 if previous else 1
        instance.code = str(date.year) + "-" + str(instance.number)
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

    credit_acc = models.FloatField(verbose_name=_("Credit accumulated"),help_text=_("Credit accumulated into the customer's account"),blank=True,null=True)

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
        self.credit_acc = self.getCreditAcc()
        self.save(update_fields=['subtotal','vat_amount','credit_acc'])

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
    
    def getCreditAcc(self):
        from myTPV.models import SiteSettings
        SETTINGS=SiteSettings.load()
        if self.bill.owner and SETTINGS.ACCUMULATION:
            if self.product.credit_acc_factor:
                return round(self.getSubtotal()*self.product.credit_acc_factor,2) 
        return None

    def getVATAmount(self):
        if self.vat_amount:
            refunded = (self.refund.quantity*self.vat_amount/self.quantity) if hasattr(self, "refund") else 0
            return round(self.vat_amount - refunded,2)
        else:
            if self.product.promotion:
                promotion_quantity = self.product.promotion.getEffectiveQuantity(quantity = self.quantity)
                return round(promotion_quantity*self.product.getVATAmount(),2)
            return round(self.quantity*self.product.getVATAmount(),2)
        
    def getSubtotal(self,noRefunds=False):
        if self.subtotal:
            if noRefunds:
                refunded=0
            else:
                refunded = (self.refund.subtotal) if hasattr(self, "refund") else 0
            return round(self.subtotal - refunded,2)
        else:
            if self.product.promotion:
                promotion_quantity = self.product.promotion.getEffectiveQuantity(quantity = self.quantity)
                return round(promotion_quantity*self.product.pvp,2)
            return round(self.quantity*self.product.pvp,2)
    
    def getUnitPVP(self):
        return round(self.getSubtotal(noRefunds=True)/(self.quantity),2)
    
    @property
    def effectiveQuantity(self):
        refunded = (self.refund.quantity) if hasattr(self, "refund") else 0
        return self.quantity-refunded
        
    @property
    def hasRefund(self):
        return hasattr(self, "refund")
    
class Refund(models.Model):
    bill_pos = models.OneToOneField(BillPosition, on_delete=models.CASCADE,primary_key=True,)
    quantity = models.PositiveSmallIntegerField(default=1,verbose_name=_("Quantity"))
    
    def increaseQuantity(self,amount=1):
        self.quantity += amount
        self.save(update_fields=['quantity',])
        self.bill_pos.product.increase_stock(quantity=amount)
        
    @property
    def subtotal(self,):
        return round(self.quantity*self.bill_pos.subtotal/self.bill_pos.quantity,2)

@receiver(post_save, sender=Refund, dispatch_uid="update_stock_onRefundCreation")
def update_stock_onRefundCreation(sender, instance, created, **kwargs):
    if created:
        instance.bill_pos.product.increase_stock(quantity=1)