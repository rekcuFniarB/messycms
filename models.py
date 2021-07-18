from django.db import models
from django.contrib.auth.models import AbstractUser
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.timezone import now
from django.utils.text import slugify
from django.urls import reverse
from . import plugins
import json

class User(AbstractUser):
    pass

class Article(MPTTModel):
    _pageconf = None
    _request = None
    
    title = models.CharField(max_length=255, default='', blank=True)
    ## Custom title to show in menu
    menu_title = models.CharField(max_length=255, default='', blank=True)
    short = models.CharField(max_length=255, default='', blank=True)
    ## Not not using SlugField and not making it unique because it may appear with same name in 
    ## different tree level. Instead we prepare it in self.save().
    slug = models.CharField(max_length=255, default='', blank=True)
    fmt = models.CharField(
        max_length = 32,
        choices = plugins.get_list(),
        default = plugins.get_list()[0][0],
        verbose_name = 'Type'
    )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=now)
    show_in_menu = models.BooleanField(default=False)
    ## Is article available?
    available = models.BooleanField(default=True)
    content = models.TextField(default='', blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    ## Link to tree part, may be used in blocks
    link = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        self.slug = plugins.slugify(self.slug)
        
        if not self.slug and self.fmt.startswith('.'):
            self.slug = self.fmt
        
        if self.fmt == '.pageconf':
            self.slug = self.fmt
            self.available = False
            self.show_in_menu = False
        
        super().save(*args, **kwargs)
    
    @property
    def pageconf(self):
        '''
        Page attributes.
        '''
        if not self._pageconf:
            self._pageconf = self.get_children().filter(fmt='.pageconf').first()
            if self._pageconf:
                self._pageconf = self._pageconf.get_children().filter(available=True)
                for item in self._pageconf:
                    ## Preparing content properties
                    name = plugins.slug2name(item.slug)
                    if name:
                        if item.fmt == '.property':
                            if not hasattr(self._pageconf, name):
                                value = item.content.strip()
                                
                                if not value:
                                    value = item.short.strip()
                                
                                if value:
                                    try:
                                        value = json.loads(value)
                                    except:
                                        pass
                                    
                                    setattr(self._pageconf, name, value)
                        else:
                            setattr(self._pageconf, name, item)
            else:
                self._pageconf = ()
        return self._pageconf
    
    def prop(self, name, default=None):
        '''
        Properties getter. Returns default value if property not exists.
        '''
        return getattr(self.pageconf, name, default)
    
    def get_absolute_url(self):
        '''
            Builds URL path of item.
        '''
        ancestors = self.get_ancestors(include_self=True).values()
        slugs = []
        for item in ancestors:
            slug = item['slug']
            #if not slug:
            #    slug = item['menu_title']
            #if not slug:
            #    slug = item['title']
            ## It was bad idea. It's better just to use id if slug is not defined.
            if not slug:
                slug = str(item['id'])
            
            slugs.append(plugins.slugify(slug))
        
        return reverse('messcms-article-by-path', kwargs={'path': '/'.join(slugs)})
    
    
    def __str__(self):
        '''
        Text representation for list in admin interfase
        '''
        if self.slug.startswith('.'):
            return self.slug
        else:
            return '%s: %s' % (self.id, self.title or self.menu_title or self.short or self.slug)

#class PageConf():
    #__data__ = None
    
    #def __init__(self, data):
        #if not data:
            #data = {}
        #self.__dict__ = data
    
    #def __call__(self):
        #return self.__dict__
    
    #def __bool__(self):
        #return bool(self.__dict__)
    
    #def __iter__(self):
        #if type(self.__dict__) is dict:
            #return iter(self.__dict__)
        #else:
            #return self.__dict__
