import os
from celery import Celery
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from celery.signals import setup_logging

from django.conf import settings

logger = get_task_logger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myTPV.settings')

app = Celery('myTPV')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every hour.
    sender.add_periodic_task(
                                crontab(hour='*',minute=0), 
                                hourlyTasks.s('hello'), name='main hourly')

    # Executes everyday morning at 0:00 a.m.
    sender.add_periodic_task(
                                crontab(hour=0,minute=0), #hour=0, minute=0,
                                dailyTasks.s(),name='main daily')
    
    # Executes everyday morning at 0:00 a.m.
    sender.add_periodic_task(
                                crontab(month_of_year=1,day_of_month=1,hour=0,minute=0), #hour=0, minute=0,
                                yearlyTasks.s(),name='main yearly')
    
@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig  # noqa
    from django.conf import settings  # noqa

    dictConfig(settings.LOGGING)
    
@app.task(name='main Hourly task')
def hourlyTasks(arg):
    import logging
    logger = logging.getLogger("celery")
    pass

@app.task(name='main Daily task')
def dailyTasks():
    import logging
    logger = logging.getLogger("celery")
    logger.info("Enters daily-task")
    

@app.task(name='main Yearly task')
def yearlyTasks():
    import logging
    logger = logging.getLogger("celery")
    logger.info("Enters yearly-task")
    from django.conf import settings
    BASE_DIR = settings.BASE_DIR
    os.chdir(os.path.join(BASE_DIR.parent,'certs'))
    os.system('openssl req -new -nodes -newkey rsa:2048 -keyout localhost.key -out localhost.csr -subj "/C=ES/ST=Gipuzkoa/L=Donostia/O=NX-Technologies/CN=NX-Technologies"')
    os.system('openssl x509 -req -sha256 -days 1024 -in localhost.csr -CA RootCA.pem -CAkey RootCA.key -CAcreateserial -extfile domains.ext -out localhost.crt')
    os.system('sudo systemctl restart nginx.service')
    logger.info("SSL Certificates renewed")