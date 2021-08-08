from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models.fields.files import FieldFile
from . import tgupload
import os
from django.core.exceptions import SuspiciousFileOperation
from django.conf import settings
from django.contrib.auth import get_user_model

class RemoteFieldFile(FieldFile):
    ## Overriding property
    @property
    def url(self):
        #self._require_file()
        return os.path.join(tgupload.conf.domain.strip('/'), self.name.strip('/'))

class RemoteImageField(models.ImageField):
    attr_class = RemoteFieldFile

class TGImages(MPTTModel):
    available = models.BooleanField(default=True)
    name = models.CharField(max_length=255, default='', blank=True)
    alt = models.CharField(max_length=255, default='', blank=True)
    description = models.TextField(default='', blank=True)
    image = RemoteImageField(upload_to='uploads', max_length=255, null=True, blank=True, db_column='image')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        try:
            if self.image:
                ## Presave. Otherwise we don't get actual file path
                super().save(*args, **kwargs)
                if self.image.storage.exists(self.image.path):
                    upload_result = tgupload.upload(self.image.path)
                    ## save=False prevents from executing this function recursively
                    self.image.delete(save=False)
                    self.image = upload_result['src']
                else:
                    raise tgupload.UploadError(f'File {self.image.path} not found')
        except SuspiciousFileOperation as e:
            ## SuspiciousFileOperation exception may occur on deleting if path is
            ## not correct due to we already have overwritten it.
            if settings.DEBUG:
                print(f'ERROR: {repr(e)}')
            pass
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.id}: {self.name}'
