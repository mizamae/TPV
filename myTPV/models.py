from django.core.cache import cache
from django.db import models
from django.db.utils import OperationalError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging
logger = logging.getLogger("models")

class SingletonModel(models.Model):
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)
        self.set_cache()
    
    def set_cache(self):
        cache.set(self.__class__.__name__, self)
    
    @classmethod
    def checkIfExists(cls):
        try:
            obj = cls.objects.get(pk=1)
            return True
        except cls.DoesNotExist:
            return False
    
    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            obj.set_cache()
        return cache.get(cls.__name__)
    
class SiteSettings(SingletonModel):
    class Meta:
        verbose_name = _('Configuration')
        verbose_name_plural = _('Configurations')

    SHOP_NAME = models.CharField(verbose_name=_('Name of the shop'),max_length=100,
                                    help_text=_('The name of the shop'),default='My shop')
    VERSION_AUTO_UPDATE=models.BooleanField(verbose_name=_('Automatic updates'),
                                help_text=_('Allows to automatically update the software from official repository (requires internet access)'),default=False)
    VERSION_CODE= models.CharField(verbose_name=_('Code of the current version'),
                                max_length=10,default='',blank=True)

    LAN_IP = models.GenericIPAddressField(blank=True, null=True)

    SEC2LOGOUT = models.PositiveSmallIntegerField(verbose_name=_("Seconds to logout"),default=0,
                                                 help_text=_("Seconds after when, the user would need to login again"))
    
    VAT = models.FloatField(verbose_name=_("VAT"),help_text=_("Percentage of the cost added as a tax"),default=21.0)

    @classmethod
    def runOnInit(cls):
        connected = cls.checkInternetConnection()
        IP=cls.getMyLANIP()
        SETTINGS=cls.load()
        if IP != SETTINGS.LAN_IP:
            SETTINGS.LAN_IP = IP
            SETTINGS.save(update_fields=['LAN_IP',])
        
        from git import Repo
        repo = Repo(settings.GIT_PATH)
        res=repo.remotes.origin.pull('main')
        try:
            rev_code = res[0].commit.name_rev
        except: 
            rev_code = 'unknown'
        if rev_code[0:7] != SETTINGS.VERSION_CODE:
            SETTINGS.VERSION_CODE = rev_code[0:7]
            SETTINGS.save(update_fields=['VERSION_CODE',])

    @staticmethod
    def checkInternetConnection():
        import requests
        try:
            r = requests.get('http://google.com',timeout=1)
            if r.status_code==200:
                return True
            else:
                return False
        except: 
            return False
    
    @staticmethod
    def getMyLANIP():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('192.0.0.8', 1027))
        except socket.error:
            return None
        return s.getsockname()[0]