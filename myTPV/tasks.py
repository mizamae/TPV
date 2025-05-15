from celery import shared_task
import logging
logger = logging.getLogger("celery")
from git import Repo
from django.conf import settings
import re    
from sys import stdout as sys_stdout
from subprocess import Popen, PIPE

@shared_task(bind=False,name='mainAPP_checkRepository')
def checkRepository(force=False):
     from .models import SiteSettings
     SETTINGS = SiteSettings.load()
     if SETTINGS.VERSION_AUTO_UPDATE or force:
          repo = Repo(settings.GIT_PATH)
          res=repo.remotes.origin.pull('main')
          try:
               commiter = res[0].commit.committer.email
               rev_code = res[0].commit.name_rev
               summary = res[0].commit.summary
          except: 
               pass
          logger.info("Repository updated OK")
          logger.info("Creating migrations")
          process = Popen(settings.PYTHON_PATH+" manage.py makemigrations", cwd=settings.GIT_PATH, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
          stdout, err = process.communicate()
          if not 'No changes detected' in stdout:
               logger.info('Created new migrations ' + str(stdout))
               
          # CHECK IF THERE IS ANY UNAPPLIED MIGRATION
          process = Popen(settings.PYTHON_PATH+" manage.py showmigrations --list", cwd=settings.GIT_PATH, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
          stdout, err = process.communicate()
          if err and (not 'UserWarning: ' in err):
               logger.error('MIGRATIONS CHECK ERROR: ' + str(err))
               
          migrations= "[ ]" in stdout

          if migrations:
               logger.debug('MIGRATIONS: ' + str(stdout))
               process = Popen(settings.PYTHON_PATH+" manage.py migrate", cwd=settings.GIT_PATH, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
               stdout, err = process.communicate()
               if (not err) or ('UserWarning' in err):
                    logger.info("Django DB updated OK")
               else:
                    logger.error('MIGRATIONS APPLICATION ERROR: ' + str(err))
                    return
          else:
               logger.info("This update did not require migrating the DB")

          # UPDATE STATIC FILES
          process = Popen(settings.PYTHON_PATH+" manage.py collectstatic --noinput", cwd=settings.GIT_PATH, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
          stdout, err = process.communicate()
          
          if 'static files copied to' in stdout and stdout[0]!='0':
               logger.info("Static files copied")
          elif not 'UserWarning' in err:
               logger.error("Error copying static files - "+ str(err))

          logger.info("Restarting celery")
          process = Popen("sudo systemctl restart celery_*", cwd=settings.GIT_PATH, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
          stdout, err = process.communicate()

          logger.info("Restarting gunicorn")
          process = Popen("sudo systemctl restart gunicorn", cwd=settings.GIT_PATH, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
          stdout, err = process.communicate()
            