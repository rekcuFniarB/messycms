from django.db import models
from django.contrib.auth.models import AbstractUser
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.timezone import now

class User(AbstractUser):
    pass

class Article(MPTTModel):
    title = models.CharField(max_length=255)
    short = models.CharField(max_length=32)
    fmt = models.CharField(
        max_length = 3,
        choices = [
                ('htm', 'HTML'),
            ],
        default = 'htm',
        verbose_name = 'Type'
    )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=now)
    show_in_menu = models.BooleanField()
    content = models.TextField()
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    def __str__(self):
        return '%s: %s' % (self.id, self.short)
