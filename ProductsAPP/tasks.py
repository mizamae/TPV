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

@shared_task(bind=False,name='ProductsAPP_send_email')
def send_email(subject,message,recipient_list,attachments=None):
    if "gmail" in settings.EMAIL_HOST:
        from utils.googleGmail import googleGmail_handler
        googleGmail_handler.sendMultipleEmails(subject=subject,attachments=attachments,recipients=recipient_list,html_content=message)
        logger.info("Email sent to " + str(recipient_list))

@shared_task(bind=False,name='ProductsAPP_send_bill')
def sendBillReceipt(billData):
    from .models import BillAccount
    if billData['status'] == BillAccount.STATUS_PAID and billData['customer'] and billData['customer']['email']:
        from utils.pdfConverter import PrintedBill
        bill = PrintedBill(billData=billData,commerceData={'name':"Pattas S.L.",
                                                            'address1':"Avda Gipuzkoa 4",
                                                            'address2':'31187 Tolosa',
                                                            'cif':"97245623",
                                                            'phone':"944525656",
                                                            'web':'www.pattas.es'})
        with open(billData["code"]+".pdf", "wb") as binary_file:
            binary_file.write(bill.pdf)
        if "gmail" in settings.EMAIL_HOST:
            from utils.googleGmail import googleGmail_handler
            googleGmail_handler.sendEmail(subject='Invoice test',attachments=[billData["code"]+".pdf",],recipient=billData['customer']['email'],
                                          html_content='Hello darling')
        os.remove(billData["code"]+".pdf")

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
        

