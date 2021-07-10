from django.db import models
from django.contrib.auth.models import AbstractUser
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.timezone import now

class User(AbstractUser):
    pass

class Article(MPTTModel):
    title = models.CharField(max_length=255, default='')
    ## Custom title to show in menu
    menu_title = models.CharField(max_length=255, default='')
    short = models.CharField(max_length=255)
    ## Not making it unique because it may appear with same name in 
    ## different tree level.
    slug = models.CharField(max_length=255, default='')
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
    show_in_menu = models.BooleanField(default=False)
    ## Is article available?
    available = models.BooleanField(default=True)
    content = models.TextField(default='')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    def __str__(self):
        return '%s: %s' % (self.id, self.short)
