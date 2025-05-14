from celery import shared_task
import logging
logger = logging.getLogger("celery")

@shared_task(bind=False,name='UsersAPP_loadDefaultObjects')
def loadDefaultObjects():
    from .models import User
    User.loadDefaultObjects()