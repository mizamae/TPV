from celery import shared_task
from django.core.mail import send_mail, EmailMessage
from django.utils.translation import gettext as _
from django.conf import settings
from django.utils import timezone
from django.template import Context
from django.template.loader import get_template
from django.contrib.auth import get_user_model
User=get_user_model()
import logging
logger = logging.getLogger("celery")
import os
import json

__sql_createTableStatement__ = """CREATE TABLE IF NOT EXISTS jobs (
                                id INTEGER PRIMARY KEY, 
                                url text NOT NULL, 
                                data text NOT NULL
                        );"""
__sql_insertJob__ = ''' INSERT INTO jobs(url,data)
                        VALUES(?,?) '''

@shared_task(bind=False,name='ProductsAPP_send_bill')
def sendBillReceipt(billData):
    from .models import BillAccount
    from myTPV.models import SiteSettings
    SETTINGS = SiteSettings.load()
    if billData['status'] == BillAccount.STATUS_PAID and billData['customer'] and billData['customer']['email']:
        from utils.pdfConverter import PrintedBill
        bill = PrintedBill(billData=billData,commerceData=SETTINGS.commerceData())
        with open(billData["code"]+".pdf", "wb") as binary_file:
            binary_file.write(bill.pdf)
        if "gmail" in settings.EMAIL_HOST:
            from utils.googleGmail import googleGmail_handler
            googleGmail_handler.sendEmail(subject='Invoice test',attachments=[billData["code"]+".pdf",],recipient=billData['customer']['email'],
                                          html_content='Hello darling')
        os.remove(billData["code"]+".pdf")
        
@shared_task(bind=False,name='ProductsAPP_printReceipt')
def printBillReceipt(billData):
    from.models import BillAccount
    from utils.usbUtils import ThermalPrinter
    printer = ThermalPrinter()
    if os.path.exists(os.path.join(settings.STATIC_ROOT,"site","logos","CompanyLogoTicketTop.jpg")):
        printer.printImage(os.path.join(settings.STATIC_ROOT,"site","logos","CompanyLogoTicketTop.jpg"))
    else:
        printer.printImage(os.path.join(settings.STATIC_ROOT,"site","logos","TinyTPV.jpg"))
        
    printer.printText("FRA. SIMPLIFICADA: " + str(billData['code']))
    printer.printText("Fecha: " + str(billData['date']).split(".")[0])
    printer.printText("----------------------------------------")
    printer.printText("CANT       ARTICULO       PVP      TOTAL")
    for pos in billData['positions']:
        printer.printText(str(pos['quantity'])+"    " + pos['product'] + "    " + str(round(pos["subtotal"]/pos['quantity'],2))+ "    " + str(pos["subtotal"]))
    printer.printText("")
    printer.printText("BASE: " + str(billData['total']-billData['vat']) + " €")
    printer.printText("IVA: " + str(billData['vat'])+ " €") 
    printer.printText("TOTAL: " + str(billData['total'])+" €")
    printer.printText("METODO DE PAGO: " + str(BillAccount.PAYMENT_TYPES[billData['paymentType']][1]))
    printer.printText("----------------------------------------")
    printer.printText("Plazo maximo de devolucion 15 dias")
    printer.cutPaper()
    del printer

@shared_task(bind=False,name='ProductsAPP_publish_pendingJobs')
def publish_pendingJobs():
    import sqlite3
    from myTPV.models import SiteSettings
    SETTINGS = SiteSettings.load()
    if SETTINGS.PUBLISH_TO_WEB:
        try:
            conn = sqlite3.connect("publish_pending_db.sqlite")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs order by id")
            jobs = cursor.fetchall()
            cursor.execute("DELETE FROM jobs")
            conn.commit()
        finally:
            if conn:
                conn.close()
        import requests
        from itsdangerous.serializer import Serializer
        for job in jobs:
            # job = (1, 'http://127.0.0.1:8000/products/updateproduct', '{"id": 159, "pvp": 4.36, "stock": 15}')
            try:
                url = job[1]
                data = json.loads(job[2])
                s = Serializer(settings.SIGNATURE_KEY)
                signature = json.dumps(data)
                data2send = s.dumps(signature)
                response = requests.post(url,json=data2send)
                # response = requests.post("https://"+SETTINGS.SHOP_WEB+"/products/update",json=data2send)
                logger.info("RECV " + SETTINGS.SHOP_WEB+" responded with code " + str(response.status_code) + " to publish " + str(data['id']))
                if response.status_code > 201:
                    addPendingJob(details={'url':url,'data' : data})
            except Exception as exc:
                logger.error("Failure to publish: " + str(exc))
                if data:
                    addPendingJob(details={'url':url,'data' : data})
            

def addPendingJob(details):
    import sqlite3
    try:
        conn = sqlite3.connect("publish_pending_db.sqlite")
        cursor = conn.cursor()
        cursor.execute(__sql_createTableStatement__)
        cursor.execute(__sql_insertJob__, (details['url'],json.dumps(details['data'])))
        conn.commit()
    finally:
        if conn:
            conn.close()

@shared_task(bind=False,name='ProductsAPP_publish_familyUpdates')
def publish_familyUpdates(family_id,update_fields=None):
    from .models import ProductFamily
    from myTPV.models import SiteSettings
    SETTINGS = SiteSettings.load()
    if SETTINGS.PUBLISH_TO_WEB:
        import requests
        from itsdangerous.serializer import Serializer
        url = "http://127.0.0.1:8000/products/updatefamily"
        try:
            data = ProductFamily.objects.get(id = family_id).serialize(update_fields=update_fields)
            s = Serializer(settings.SIGNATURE_KEY)
            signature = json.dumps(data)
            data2send = s.dumps(signature)
            response = requests.post(url,json=data2send)
            # response = requests.post("https://"+SETTINGS.SHOP_WEB+"/products/update",json=data2send)
            logger.info("RECV " + SETTINGS.SHOP_WEB+" responded with code " + str(response.status_code) + " to publish " + str(data['id']))
            if response.status_code > 201:
                addPendingJob(details={'url':url,'data' : data})
        except Exception as exc:
            logger.error("Failure to publish: " + str(exc))
            if data:
                addPendingJob(details={'url':url,'data' : data})


@shared_task(bind=False,name='ProductsAPP_publish_familyDelete')
def publish_familyDelete(id):
    from myTPV.models import SiteSettings
    SETTINGS = SiteSettings.load()
    if SETTINGS.PUBLISH_TO_WEB:
        import requests
        from itsdangerous.serializer import Serializer
        url = "http://127.0.0.1:8000/products/deletefamily"
        try:
            data = {'id':id}
            s = Serializer(settings.SIGNATURE_KEY)
            signature = json.dumps(data)
            data2send = s.dumps(signature)
            response = requests.post(url,json=data2send)
            # response = requests.post("https://"+SETTINGS.SHOP_WEB+"/products/update",json=data2send)
            logger.info("RECV " + SETTINGS.SHOP_WEB+" responded with code " + str(response.status_code) + " to deletion of family " + str(data['id']))
            if response.status_code > 201:
                addPendingJob(details={'url':url,'data' : data})
        except Exception as exc:
            logger.error("Failure to publish: " + str(exc))
            if data:
                addPendingJob(details={'url':url,'data' : data})

@shared_task(bind=False,name='ProductsAPP_publish_productUpdates')
def publish_productUpdates(product_id,update_fields=None):
    from .models import Product
    from myTPV.models import SiteSettings
    SETTINGS = SiteSettings.load()
    if SETTINGS.PUBLISH_TO_WEB:
        import requests
        from itsdangerous.serializer import Serializer
        url = "http://127.0.0.1:8000/products/updateproduct"
        try:
            data = Product.objects.get(id = product_id).serialize(update_fields=update_fields)
            s = Serializer(settings.SIGNATURE_KEY)
            signature = json.dumps(data)
            data2send = s.dumps(signature)
            response = requests.post(url,json=data2send)
            # response = requests.post("https://"+SETTINGS.SHOP_WEB+"/products/update",json=data2send)
            logger.info("RECV " + SETTINGS.SHOP_WEB+" responded with code " + str(response.status_code) + " to publish " + str(data['id']))
            if response.status_code > 201:
                addPendingJob(details={'url':url,'data' : data})
        except Exception as exc:
            logger.error("Failure to publish: " + str(exc))
            if data:
                addPendingJob(details={'url':url,'data' : data})

@shared_task(bind=False,name='ProductsAPP_publish_productDelete')
def publish_productDelete(product_id):
    from myTPV.models import SiteSettings
    SETTINGS = SiteSettings.load()
    if SETTINGS.PUBLISH_TO_WEB:
        import requests
        from itsdangerous.serializer import Serializer
        url = "http://127.0.0.1:8000/products/deleteproduct"
        try:
            data = {'id':product_id}
            s = Serializer(settings.SIGNATURE_KEY)
            signature = json.dumps(data)
            data2send = s.dumps(signature)
            response = requests.post(url,json=data2send)
            # response = requests.post("https://"+SETTINGS.SHOP_WEB+"/products/update",json=data2send)
            logger.info("RECV " + SETTINGS.SHOP_WEB+" responded with code " + str(response.status_code) + " to deletion of " + str(data['id']))
            if response.status_code > 201:
                addPendingJob(details={'url':url,'data' : data})
        except Exception as exc:
            logger.error("Failure to publish: " + str(exc))
            if data:
                addPendingJob(details={'url':url,'data' : data})

@shared_task(bind=False,name='ProductsAPP_send_email')
def send_email(subject,message,recipient_list,attachments=None):
    if "gmail" in settings.EMAIL_HOST:
        from utils.googleGmail import googleGmail_handler
        googleGmail_handler.sendMultipleEmails(subject=subject,attachments=attachments,recipients=recipient_list,html_content=message)
        logger.info("Email sent to " + str(recipient_list))

@shared_task(bind=False,name='ProductsAPP_monthly_results')
def monthly_results():
    from .models import Consumible
    now=timezone.now().date()
    month = now.month
    year = now.year
    if month==1:
        month=12
        year-=1
    else:
        month-=1
    
    subject=_('[MONTHLY_RESULTS] Results of the month ' + str(month) + ' of ' + str(year))
    consumibles = Consumible.objects.all()
    
    total_ingress = Consumible.get_monthly_ingress(month,year)
    total_cost = Consumible.get_monthly_cost(month,year)

    message = get_template("ProductsAPP/_monthlyreport_mailtemplate.html").render({
        'consumibles': consumibles,
        'heading':subject,
        'month':month,
        'year':year,
        'total_cost':total_cost,
        'total_ingress':total_ingress,
        'benefit':total_ingress-total_cost
    })

    recipients=User.getStaffEmails()
    logger.info("Direcciones del personal staff " + str(recipients))

    if recipients!=[]:
        send_email(subject,message,from_email=settings.EMAIL_HOST_USER,recipient_list=recipients)
    
    

@shared_task(bind=False,name='ProductsAPP_checkstocks')
def check_stock_level():
    from .models import Consumible
    warning = []
    message=_('The following consumables are below its safety stock level:')
    consumibles = Consumible.objects.all()

    now=timezone.now().date()
    month = now.month
    year = now.year

    for consumible in consumibles:
        monthly_consumption = Consumible.get_monthly_consumption(instance=consumible,month=month,year=year)
        if consumible.stock <= consumible.stock_min:
            warning.append(consumible.name)
            message+='\n'+_('\t- ' + str(consumible)+' has a stock of '+str(consumible.stock))
    
    if warning !=[]:
        recipients=User.getStaffEmails()
        logger.info("Direcciones del personal staff " + str(recipients))
        logger.info(message)
        if recipients!=[]:
            send_email(subject=_('[STOCK_WARNING] List of the products with stock below its minimum'),
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=recipients)
    else:
        logger.info("Comprobado niveles de stock y todo esta OK")
        

