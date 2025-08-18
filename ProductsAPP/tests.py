from django.test import tag,TestCase,Client, TransactionTestCase
from time import sleep
from django.utils import timezone
from django.core.cache import cache
from celery.contrib.testing.worker import start_worker
from myTPV.celery import app
from django.forms import ValidationError
import copy
from .models import VATValue, Manufacturer, ProductFamily, Consumible, Product, CombinationPosition, ProductDiscount, ProductPromotion, BillAccount
from UsersAPP.models import Customer, User, CustomerProfile

print('######################################')
print('# TESTING OF ProductsAPP MODEL FUNCTIONS #')
print('######################################')

def createManufacturers():
    names = ["Manufacturer 1","Manufacturer 2","Manufacturer 3","Manufacturer 4"]
    for name in names:
        Manufacturer.objects.create(name=name)
    
        

def createProductFamilies():
    names = ["Comida perros","Comida gatos","Comida pajaros","Comida peces"]
    for name in names:
        ProductFamily.objects.create(name=name)

def createConsumables():
    consumables = [
                    {"name":"Consumable "+str(i),"barcode":"456456465"+str(i),"family":ProductFamily.objects.get(id=i%4+ProductFamily.objects.order_by('id').first().id),
                     "manufacturer":Manufacturer.objects.get(id=i%4+Manufacturer.objects.order_by('id').first().id),
                     "cost":100,"price":200,"order_quantity":10,"stock":100,"stock_min":10,"generates_product":True}
                    for i in range (30)    
                ]
    for consumable in consumables:
        Consumible.objects.create(**consumable)

def createCompoundProducts():
    product = Product.objects.create(barcode='45645000',name="Compound product",family=ProductFamily.objects.order_by('id').first())
    CombinationPosition.objects.create(product=product,quantity=1,ingredient=Consumible.objects.order_by('id').first())
    CombinationPosition.objects.create(product=product,quantity=2,ingredient=Consumible.objects.order_by('id').last())


@tag('CostPrices')
class CostPrices_tests(TransactionTestCase):
    ''' ASPECTS ALREADY TESTED:
        - Checks every product has its cache key
        - Checks the creation of Consumables directly sellable create corresponding Products
        - Checks the correct calculation of cost on Products
        - Checks the correct calculation of cost on compound Products
        - Checks the correct calculation of price on Products
        - Checks the correct calculation of price on compound Products
        - Checks the correct calculation of pvp on Products
        - Checks the correct calculation of pvp on compound Products
    '''
    fixtures=[]
    
    ''' 
    When model instances are modified in celery tasks, you have to fork the celery worker from the django test process in order to force
    celery to use django's test db.
    In this case, the tests classes need to inherit from TransactionTestCase and a small sleep time needs to be included between the operation
    that sends the celery task and the assertion of the result in order to leave time for the celery task to execute.
    
    '''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.celery_worker = start_worker(app,perform_ping_check=False)
        cls.celery_worker.__enter__()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.celery_worker.__exit__(None, None, None)

    def setUp(self):
        cache.clear()
        self.defaultVAT, _ = VATValue.objects.get_or_create(**{"id":1,"name":"Standard","pc_value":21})
        cache.set("DefaultVAT",self.defaultVAT.pc_value,None)

        self.discount10pc = ProductDiscount.objects.create(percent=10)
        cache.set("consumable_info",{},None)
        cache.set("products_info",{},None)
        createManufacturers()
        createProductFamilies()
        createConsumables()
        createCompoundProducts()

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
             
# INDIVIDUAL FUNCTIONS TESTING
    def test_1(self):

        print('## Checks every product has its cache key ##')
        cached = cache.get("products_info")
        for product in Product.objects.all():
            self.assertTrue(product.id in cached.keys())

        print('## Checks the creation of Consumables directly sellable create corresponding Products ##')
        self.assertEqual(Product.objects.filter(single_ingredient=True).count(),Consumible.objects.filter(generates_product=True).count())
        
        print('## Checks the correct calculation of cost on Products ##')
        product1 = Product.objects.order_by('id').first()
        consumable1 = Consumible.objects.order_by('id').first()
        self.assertEqual(product1.cost,100)
        self.assertEqual(product1.cost,consumable1.cost)
        print('## Checks the correct calculation of cost on compound Products ##')
        compoundProduct = Product.objects.get(barcode='45645000')
        self.assertEqual(compoundProduct.cost,300)
        self.assertEqual(compoundProduct.cost,consumable1.cost+2*Consumible.objects.order_by('id').last().cost)

        print('## Checks the correct calculation of price on Products ##')
        product1 = Product.objects.order_by('id').first()
        consumable1 = Consumible.objects.order_by('id').first()
        self.assertEqual(product1.price,200)
        self.assertEqual(product1.price,consumable1.price)
        print('## Checks the correct calculation of price on compound Products ##')
        compoundProduct = Product.objects.get(barcode='45645000')
        self.assertEqual(compoundProduct.price,600)
        self.assertEqual(compoundProduct.price,consumable1.price+2*Consumible.objects.order_by('id').last().price)

        print('## Checks the correct calculation of pvp on Products ##')
        product1 = Product.objects.order_by('id').first()
        consumable1 = Consumible.objects.order_by('id').first()
        self.assertEqual(product1.pvp,round(200*1.21,2))
        self.assertEqual(product1.pvp,consumable1.price*(1+self.defaultVAT.pc_value/100))
        print('## Checks the correct calculation of pvp on compound Products ##')
        compoundProduct = Product.objects.get(barcode='45645000')
        self.assertEqual(compoundProduct.pvp,round(600*1.21,2))
        self.assertEqual(compoundProduct.pvp,(consumable1.price+2*Consumible.objects.order_by('id').last().price)*(1+self.defaultVAT.pc_value/100))


@tag('Bills')
class Billing_tests(TransactionTestCase):
    ''' ASPECTS ALREADY TESTED:
    Bill open
        - Bill creation and customer assignation
        - Append a position
        - Stock of the product is reduced correctly
        - VAT amount calculation
        - TOTAL amount calculation
        - Append a second position
        - Price before VAT calculation with 2 positions
        - VAT amount calculation with 2 positions
        - TOTAL amount calculation with 2 positions
        - Price before VAT calculation with 2 positions and discount
        - VAT amount calculation with 2 positions and discount
        - TOTAL amount calculation with 2 positions and discount
        - Append a position with promotion
        - Total is correctly calculated with the units equal units_take of promotion
        - Total is correctly calculated with the units bigger than units_take of promotion
        - Total is correctly calculated with the units twice units_take of promotion
    Bill closed and paid
        - Closes the bill
        - total and vat_amount fields are filled with current values (with product discount)
        - Positions also close fixing its pvp field
        - Discount eliminated but positions retain its actual pvp value
        - total and vat_amount fields are filled with current values (with product promotion)
        
    '''
    fixtures=[]
    
    ''' 
    When model instances are modified in celery tasks, you have to fork the celery worker from the django test process in order to force
    celery to use django's test db.
    In this case, the tests classes need to inherit from TransactionTestCase and a small sleep time needs to be included between the operation
    that sends the celery task and the assertion of the result in order to leave time for the celery task to execute.
    
    '''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.celery_worker = start_worker(app,perform_ping_check=False)
        cls.celery_worker.__enter__()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.celery_worker.__exit__(None, None, None)

    def setUp(self):
        cache.clear()
        self.defaultVAT, _ = VATValue.objects.get_or_create(**{"id":1,"name":"Standard","pc_value":21})
        cache.set("DefaultVAT",self.defaultVAT.pc_value,None)
        self.discount10pc = ProductDiscount.objects.create(percent=10)
        self.promotion3x2 = ProductPromotion.objects.create(**{'units_take':3,'units_pay':2})
        cache.set("consumable_info",{},None)
        cache.set("products_info",{},None)
        
        createManufacturers()
        createProductFamilies()
        createConsumables()
        createCompoundProducts()

        prof = CustomerProfile.objects.create(name="VIP",percent=10)
        self.vip_customer = Customer.objects.create(**{'first_name':'VIP customer','last_name':'customers lastname',
                                                'email':'VIPcustomer@customers.com','cif':'A123456789VIP','saves_paper':True,
                                                'profile':prof})
        
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
        stock_prev = product1.stock
        print('## Stock of the product is reduced correctly ##')
        self.assertEqual(stock_prev,100)
        bill.add_bill_position(product=product1,quantity=1)
        self.assertEqual(product1.stock,99)
        print('## VAT amount calculation ##')
        self.assertEqual(bill.getVATAmount(),round(200*0.21,2))
        self.assertEqual(product1.getVATAmount(),bill.getVATAmount())
        print('## TOTAL amount calculation ##')
        self.assertEqual(bill.total,round(200*1.21,2))
        self.assertEqual(product1.pvp,bill.total)

        print('## Append a second position ##')
        product2 = Product.objects.get(id=2)
        bill.add_bill_position(product=product2,quantity=2)
        print('## VAT amount calculation with 2 positions ##')
        self.assertEqual(bill.getVATAmount(),round(600*0.21,2))
        self.assertEqual(product1.getVATAmount()+2*product2.getVATAmount(),bill.getVATAmount())
        print('## TOTAL amount calculation with 2 positions ##')
        self.assertEqual(bill.total,round(600*1.21,2))
        self.assertEqual(product1.pvp+2*product2.pvp,bill.total)

        product1.discount = self.discount10pc
        product1.save()
        bill.bill_positions.first().set_quantity(quantity=1) # to update the discount
        print('## VAT amount calculation with 2 positions and discount ##')
        self.assertEqual(bill.getVATAmount(),round(580*0.21,2))
        self.assertEqual(product1.getVATAmount()+2*product2.getVATAmount(),bill.getVATAmount())
        print('## TOTAL amount calculation with 2 positions and discount ##')
        self.assertEqual(bill.total,round(580*1.21,2))
        self.assertEqual(product1.pvp+2*product2.pvp,bill.total)

        print('## Closes the bill ##')
        bill.paymenttype = BillAccount.PAYMENTTYPE_CASH
        bill.save(update_fields=['paymenttype',])
        bill.close()
        print('## total and vat_amount fields are filled with current values  ##')
        self.assertEqual(bill.status,BillAccount.STATUS_PAID)
        self.assertEqual(bill.total,701.8)
        self.assertEqual(bill.total*100/121*0.21,bill.getVATAmount())
        print('## Positions also close fixing its pvp field ##')
        product1.discount = None
        product1.save()
        print('## Discount eliminated but positions retain its actual pvp value ##')
        positions = bill.bill_positions.all()
        self.assertEqual(positions[0].getSubtotal(),round(0.9*positions[0].product.pvp,2))
        self.assertEqual(positions[1].getSubtotal(),round(2*positions[1].product.pvp,2))

    def test_2(self):
        bill=BillAccount.create(createdBy=self.cashier)

        print('## Append a position with promotion ##')
        product1 = Product.objects.order_by('id').first()
        product1.promotion = self.promotion3x2
        product1.save()

        print('## Total is correctly calculated with the units equal units_take of promotion ##')
        bill.add_bill_position(product=product1,quantity=3)
        self.assertEqual(bill.total,2*round(200*1.21,2))
        self.assertEqual(2*product1.pvp,bill.total)

        print('## Total is correctly calculated with the units bigger than units_take of promotion ##')
        bill.add_bill_position(product=product1,quantity=2)
        self.assertEqual(bill.total,4*round(200*1.21,2))
        self.assertEqual(4*product1.pvp,bill.total)

        print('## Total is correctly calculated with the units twice units_take of promotion ##')
        bill.add_bill_position(product=product1,quantity=1)
        self.assertEqual(bill.total,4*round(200*1.21,2))
        self.assertEqual(4*product1.pvp,bill.total)

        print('## Closes the bill ##')
        bill.paymenttype = BillAccount.PAYMENTTYPE_CASH
        bill.save(update_fields=['paymenttype',])
        bill.close()

        product1.promotion = None
        product1.save()
        print('## total and vat_amount fields are filled with current values  ##')
        self.assertEqual(bill.total,4*round(200*1.21,2))
        self.assertEqual(bill.total*100/121*0.21,bill.getVATAmount())

    def test_3(self):
        bill=BillAccount.create(createdBy=self.cashier)

        print('## Append a position ##')
        product1 = Product.objects.order_by('id').first()

        print('## Total is correctly calculated without customer ##')
        bill.add_bill_position(product=product1,quantity=2)
        self.assertEqual(bill.total,2*round(200*1.21,2))
        self.assertEqual(2*product1.pvp,bill.total)

        print('## Total is correctly calculated with a VIP customer ##')
        bill.setOwner(customer=self.vip_customer)
        self.assertEqual(bill.total,2*0.9*round(200*1.21,2))
        self.assertEqual(2*0.9*product1.pvp,bill.total)
