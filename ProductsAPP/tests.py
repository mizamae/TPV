from django.test import tag,TestCase,Client
from time import sleep
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.models import User
from django.forms import ValidationError
import copy
from .models import VATValue, ProductFamily, Consumible, Product, CombinationPosition, ProductDiscount, BillAccount

print('######################################')
print('# TESTING OF ProductsAPP MODEL FUNCTIONS #')
print('######################################')

def createProductFamilies():
    names = ["Comida perros","Comida gatos","Comida pajaros","Comida peces"]
    for name in names:
        ProductFamily.objects.create(name=name)

def createConsumables():
    consumables = [
                    {"name":"Consumable "+str(i),"barcode":"456456465"+str(i),"family":ProductFamily.objects.get(id=i%4+1),"cost":100+i,"price":200+i,"order_quantity":10,"stock":100,"stock_min":10,"generates_product":True}
                    for i in range (30)    
                ]
    for consumable in consumables:
        Consumible.objects.create(**consumable)

def createCompoundProducts():
    product = Product.objects.create(barcode='45645000',name="Compound product",family=ProductFamily.objects.get(id=1))
    CombinationPosition.objects.create(product=product,quantity=1,ingredient=Consumible.objects.get(id=1))
    CombinationPosition.objects.create(product=product,quantity=2,ingredient=Consumible.objects.get(id=2))


@tag('PartFamily')
class PartFamily_tests(TestCase):
    ''' ASPECTS ALREADY TESTED:

    '''
    fixtures=[]
    
    def setUp(self):
        self.defaultVAT, _ = VATValue.objects.get_or_create(**{"id":1,"name":"Standard","pc_value":21})
        self.discount10pc = ProductDiscount.objects.create(percent=10)
        createProductFamilies()
        createConsumables()
        createCompoundProducts()

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
             
# INDIVIDUAL FUNCTIONS TESTING
    def test_1(self):
        print('## Checks the creation of Consumables directly sellable create corresponding Products ##')
        self.assertEqual(Product.objects.filter(single_ingredient=True).count(),Consumible.objects.filter(generates_product=True).count())
        
        print('## Checks the correct calculation of cost on Products ##')
        product1 = Product.objects.get(id=1)
        consumable1 = Consumible.objects.get(id=1)
        self.assertEqual(product1.cost(),consumable1.cost)
        print('## Checks the correct calculation of cost on compound Products ##')
        compoundProduct = Product.objects.get(barcode='45645000')
        self.assertEqual(compoundProduct.cost(),consumable1.cost+2*Consumible.objects.get(id=2).cost)

        print('## Checks the correct calculation of price on Products ##')
        product1 = Product.objects.get(id=1)
        consumable1 = Consumible.objects.get(id=1)
        self.assertEqual(product1.price(),consumable1.price)
        print('## Checks the correct calculation of price on compound Products ##')
        compoundProduct = Product.objects.get(barcode='45645000')
        self.assertEqual(compoundProduct.price(),consumable1.price+2*Consumible.objects.get(id=2).price)

        print('## Checks the correct calculation of pvp on Products ##')
        product1 = Product.objects.get(id=1)
        consumable1 = Consumible.objects.get(id=1)
        self.assertEqual(product1.pvp,consumable1.price*(1+self.defaultVAT.pc_value/100))
        print('## Checks the correct calculation of pvp on compound Products ##')
        compoundProduct = Product.objects.get(barcode='45645000')
        self.assertEqual(compoundProduct.pvp,(consumable1.price+2*Consumible.objects.get(id=2).price)*(1+self.defaultVAT.pc_value/100))

        print('## Checks the correct calculation of pvp on Products with discount ##')
        product1.discount = self.discount10pc 
        consumable1 = Consumible.objects.get(id=1)
        value = consumable1.price*(1-product1.discount.percent/100+self.defaultVAT.pc_value/100)
        self.assertEqual(product1.pvp,round(value,2))
