from django.test import tag,TestCase,Client
from time import sleep
from django.utils import timezone
from django.core.cache import cache
from django.forms import ValidationError
import copy
from .models import VATValue, ProductFamily, Consumible, Product, CombinationPosition, ProductDiscount, BillAccount
from UsersAPP.models import Customer, User

print('######################################')
print('# TESTING OF ProductsAPP MODEL FUNCTIONS #')
print('######################################')

def createProductFamilies():
    names = ["Comida perros","Comida gatos","Comida pajaros","Comida peces"]
    for name in names:
        ProductFamily.objects.create(name=name)

def createConsumables():
    consumables = [
                    {"name":"Consumable "+str(i),"barcode":"456456465"+str(i),"family":ProductFamily.objects.get(id=i%4+1),"cost":100,"price":200,"order_quantity":10,"stock":100,"stock_min":10,"generates_product":True}
                    for i in range (30)    
                ]
    for consumable in consumables:
        Consumible.objects.create(**consumable)

def createCompoundProducts():
    product = Product.objects.create(barcode='45645000',name="Compound product",family=ProductFamily.objects.get(id=1))
    CombinationPosition.objects.create(product=product,quantity=1,ingredient=Consumible.objects.get(id=1))
    CombinationPosition.objects.create(product=product,quantity=2,ingredient=Consumible.objects.get(id=2))


@tag('CostPrices')
class CostPrices_tests(TestCase):
    ''' ASPECTS ALREADY TESTED:
        - Checks the creation of Consumables directly sellable create corresponding Products
        - Checks the correct calculation of cost on Products
        - Checks the correct calculation of cost on compound Products
        - Checks the correct calculation of price on Products
        - Checks the correct calculation of price on compound Products
        - Checks the correct calculation of pvp on Products
        - Checks the correct calculation of pvp on compound Products
        - Checks the correct calculation of pvp on Products with discount
        - Checks the correct calculation of pvp on compound Products with discount
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
        self.assertEqual(product1.price(),200)
        self.assertEqual(product1.price(),consumable1.price)
        print('## Checks the correct calculation of price on compound Products ##')
        compoundProduct = Product.objects.get(barcode='45645000')
        self.assertEqual(compoundProduct.price(),600)
        self.assertEqual(compoundProduct.price(),consumable1.price+2*Consumible.objects.get(id=2).price)

        print('## Checks the correct calculation of pvp on Products ##')
        product1 = Product.objects.get(id=1)
        consumable1 = Consumible.objects.get(id=1)
        self.assertEqual(product1.pvp,round(200*1.21,2))
        self.assertEqual(product1.pvp,consumable1.price*(1+self.defaultVAT.pc_value/100))
        print('## Checks the correct calculation of pvp on compound Products ##')
        compoundProduct = Product.objects.get(barcode='45645000')
        self.assertEqual(compoundProduct.pvp,round(600*1.21,2))
        self.assertEqual(compoundProduct.pvp,(consumable1.price+2*Consumible.objects.get(id=2).price)*(1+self.defaultVAT.pc_value/100))

        print('## Checks the correct calculation of pvp on Products with discount ##')
        product1.discount = self.discount10pc 
        product1.save()
        consumable1 = Consumible.objects.get(id=1)
        self.assertEqual(product1.pvp,round(200*1.21*0.9,2))
        value = consumable1.price*(1-product1.discount.percent/100)*(1+self.defaultVAT.pc_value/100)
        self.assertEqual(product1.pvp,round(value,2))
        print('## Checks the correct calculation of pvp on compound Products with discount ##')
        compoundProduct = Product.objects.get(barcode='45645000')
        compoundProduct.discount = self.discount10pc 
        compoundProduct.save()
        self.assertEqual(compoundProduct.pvp,round(600*0.9*1.21,2))
        value = (consumable1.price+2*Consumible.objects.get(id=2).price)*(1-product1.discount.percent/100)*(1+self.defaultVAT.pc_value/100)
        self.assertEqual(compoundProduct.pvp,round(value,2))

@tag('Bills')
class Billing_tests(TestCase):
    ''' ASPECTS ALREADY TESTED:
    Bill open
        - Bill creation and customer assignation
        - Append a position
        - Price before VAT calculation
        - VAT amount calculation
        - TOTAL amount calculation
        - Append a second position
        - Price before VAT calculation with 2 positions
        - VAT amount calculation with 2 positions
        - TOTAL amount calculation with 2 positions
        - Price before VAT calculation with 2 positions and discount
        - VAT amount calculation with 2 positions and discount
        - TOTAL amount calculation with 2 positions and discount
    Bill closed and paid

    '''
    fixtures=[]
    
    def setUp(self):
        self.defaultVAT, _ = VATValue.objects.get_or_create(**{"id":1,"name":"Standard","pc_value":21})
        self.discount10pc = ProductDiscount.objects.create(percent=10)
        createProductFamilies()
        createConsumables()
        createCompoundProducts()
        self.cashier = User.objects.create(**{'identifier':'cashier','first_name':'cashiers name','last_name':'cashiers lastname'})
        self.green_customer = Customer.objects.create(**{'first_name':'customers name','last_name':'customers lastname',
                                                   'email':'customers@customers.com','cif':'A2345456','saves_paper':True})

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
             
# INDIVIDUAL FUNCTIONS TESTING
    def test_1(self):
        print('## Bill creation and customer assignation ##')
        bill=BillAccount.create(createdBy=self.cashier)
        bill.setOwner(self.green_customer)

        print('## Append a position ##')
        product1 = Product.objects.get(id=1)
        bill.add_bill_position(product=product1,quantity=1)
        print('## Price before VAT calculation ##')
        self.assertEqual(bill.getTotalBeforeVAT(),200)
        self.assertEqual(product1.price(),bill.getTotalBeforeVAT())
        print('## VAT amount calculation ##')
        self.assertEqual(bill.getVATAmount(),round(200*0.21,2))
        self.assertEqual(product1.getVATAmount(),bill.getVATAmount())
        print('## TOTAL amount calculation ##')
        self.assertEqual(bill.getTotal(),round(200*1.21,2))
        self.assertEqual(product1.pvp,bill.getTotal())

        print('## Append a second position ##')
        product2 = Product.objects.get(id=2)
        bill.add_bill_position(product=product2,quantity=2)
        print('## Price before VAT calculation with 2 positions ##')
        self.assertEqual(bill.getTotalBeforeVAT(),600)
        self.assertEqual(product1.price()+2*product2.price(),bill.getTotalBeforeVAT())
        print('## VAT amount calculation with 2 positions ##')
        self.assertEqual(bill.getVATAmount(),round(600*0.21,2))
        self.assertEqual(product1.getVATAmount()+2*product2.getVATAmount(),bill.getVATAmount())
        print('## TOTAL amount calculation with 2 positions ##')
        self.assertEqual(bill.getTotal(),round(600*1.21,2))
        self.assertEqual(product1.pvp+2*product2.pvp,bill.getTotal())

        product1.discount = self.discount10pc
        product1.save()
        print('## Price before VAT calculation with 2 positions and discount ##')
        self.assertEqual(bill.getTotalBeforeVAT(),580)
        self.assertEqual(product1.price()+2*product2.price(),bill.getTotalBeforeVAT())
        print('## VAT amount calculation with 2 positions and discount ##')
        self.assertEqual(bill.getVATAmount(),round(580*0.21,2))
        self.assertEqual(product1.getVATAmount()+2*product2.getVATAmount(),bill.getVATAmount())
        print('## TOTAL amount calculation with 2 positions and discount ##')
        self.assertEqual(bill.getTotal(),round(580*1.21,2))
        self.assertEqual(product1.pvp+2*product2.pvp,bill.getTotal())

        print('## Closes the bill ##')
        bill.paymenttype = BillAccount.PAYMENTTYPE_CASH
        bill.save(update_fields=['paymenttype',])
        bill.close()
        self.assertEqual(bill.status,BillAccount.STATUS_PAID)
