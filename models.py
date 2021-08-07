from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
#from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.timezone import now
from django.utils.text import slugify
from django.urls import reverse
from . import plugins
import json
import importlib

__IMPORTED_CLASSES__ = {}

AUTH_USER_MODEL = get_user_model()

def import_class(name):
    '''
    Imports class from module and returns it. Name is string in the form of "module.classname"
    '''
    if name not in __IMPORTED_CLASSES__:
        _name = name.split('.')
        ## Expected value of "name" is "module.className"
        class_name = _name.pop()
        module_name = '.'.join(_name)
        __IMPORTED_CLASSES__[name] = getattr(importlib.import_module(module_name), class_name)
    return __IMPORTED_CLASSES__[name]

if hasattr(settings, 'MESSYCMS_BASE_MODEL'):
    ## Developer may define own models if he wants to define additional fields and methods
    Node = import_class(settings.MESSYCMS_BASE_MODEL)
else:
    class Node(MPTTModel):
        __conf = None
        title = models.CharField(max_length=255, default='', blank=True)
        ## Custom title to show in menu
        menu_title = models.CharField(max_length=255, default='', blank=True)
        short = models.CharField(max_length=255, default='', blank=True)
        ## Not not using SlugField and not making it unique because it may appear with same name in 
        ## different tree level. Instead we prepare it in self.save().
        slug = models.CharField(max_length=255, default='', blank=True)
        type = models.CharField(
            max_length = 32,
            choices = plugins.get_list(),
            default = plugins.get_list()[0][0],
            verbose_name = 'Type'
        )
        author = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
        timestamp = models.DateTimeField(default=now)
        show_in_menu = models.BooleanField(default=False)
        ## Is node available?
        available = models.BooleanField(default=True)
        content = models.TextField(default='', blank=True)
        parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
        ## Link to tree part, may be used in blocks
        link = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
        sites = models.ManyToManyField(Site, null=True, blank=True)
        
        context = {}
        
        def save(self, *args, **kwargs):
            self.slug = plugins.slugify(self.slug)
            if self.type == '.conf':
                self.slug = self.type
                self.available = False
                self.show_in_menu = False
            
            super().save(*args, **kwargs)
            
            ## If no site defined for node
            ## TODO it doesn't work here
            #if not self.sites.all():
            #    ## If have parent and parent has site defined
            #    if self.parent_id and self.parent.sites.all():
            #        ## Inherit parent node sites
            #        self.sites.add(*self.parent.sites.all())
        
        @property
        def conf(self):
            '''
            Page attributes.
            '''
            if not self.__conf:
                #self.__conf = self.get_children().filter(type='.conf').first()
                ## For some strange reason above method sometimes returns None
                ## when this function is invoked from template.
                self.__conf = Node.objects.filter(parent_id=self.id, type='.conf').first()
                
                if self.__conf:
                    self.__conf = self.__conf.get_children()
                    for item in self.__conf:
                        ## Preparing content properties
                        name = plugins.slug2name(item.slug)
                        if item.type == '.property' and name:
                            if not hasattr(self.__conf, name):
                                value = item.content.strip()
                                
                                if not value:
                                    value = item.short.strip()
                                
                                if value:
                                    if '=' in value:
                                        parsed_model = value.split('=')
                                        try:
                                            value = self.get_from_model(parsed_model[0], int(parsed_model[1]))
                                        except:
                                            pass
                                    
                                    if (type(value) is str):
                                        ## Try interpret value as JSON
                                        try:
                                            value = json.loads(value)
                                        except:
                                            pass
                                    
                                    setattr(self.__conf, name, value)
                                elif item.link_id:
                                    setattr(self.__conf, name, item.link)
                                else:
                                    setattr(self.__conf, name, None)
                                
                        elif not hasattr(self.__conf, name):
                            setattr(self.__conf, name, item)
                else:
                    self.__conf = ()
                
            return self.__conf
        
        def prop(self, name, default=None):
            '''
            Properties getter. Returns default value if property not exists.
            '''
            return getattr(self.conf, name, default)
        
        #def __get_prop(self, name, *args, **kwargs):
        #    return super().__get__(name, *args, **kwargs)
        
        def render(self):
            '''
            Lazy content rendering
            '''
            return plugins.render(None, self)
        
        def get_absolute_url(self):
            '''
                Builds URL path of item.
            '''
            ancestors = self.get_ancestors(include_self=True).values()
            slugs = []
            for item in ancestors:
                ## Skipping root directory because it used for site root.
                if item['parent_id']:
                    slug = item['slug']
                    
                    if not slug:
                        slug = item['id']
                    
                    slugs.append(slugify(slug, allow_unicode=True))
            
            if len(slugs):
                reverse_url = reverse('messycms-node-by-path', kwargs={'path': '/'.join(slugs)})
            else:
                reverse_url = reverse('messycms-root-path')
            
            return reverse_url
        
        def get_from_model(self, model_name, id):
            if type(model_name) is str:
                model_defined = False
                for app in settings.INSTALLED_APPS:
                    ## Check if model is listed in installed apps
                    if app in model_name:
                        model_defined = True
                        break
                if model_defined:
                    model = import_class(model_name)
                else:
                    if self:
                        raise self.DoesNotExist(f'No installed app for model {model_name}')
                    else:
                        raise BaseException(f'No installed app for model {model_name}')
            else:
                model = model_name
            
            return model.objects.get(pk=id)
        
        def __str__(self):
            '''
            Text representation for list in admin interfase
            '''
            if self.slug.startswith('.') or self.type.startswith('.'):
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

## Table for mamytomany sites reference. Wasn't created automatically by migrations for some reason.
#    CREATE TABLE IF NOT EXISTS "MessyCMS_node_sites" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "node_id" integer NOT NULL REFERENCES "MessyCMS_node" ("id") DEFERRABLE INITIALLY DEFERRED, "site_id" integer NOT NULL REFERENCES "django_site" ("id") DEFERRABLE INITIALLY DEFERRED);
#    CREATE UNIQUE INDEX "MessyCMS_node_sites_node_id_site_id_bc85e8ad_uniq" ON "MessyCMS_node_sites" ("node_id", "site_id");
#    CREATE INDEX "MessyCMS_node_sites_node_id_faa45963" ON "MessyCMS_node_sites" ("node_id");
#    CREATE INDEX "MessyCMS_node_sites_site_id_96701cdf" ON "MessyCMS_node_sites" ("site_id");