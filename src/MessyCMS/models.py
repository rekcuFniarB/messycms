from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
#from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.timezone import now
from django.utils.text import slugify
from django.urls import reverse
from . import plugins
import json

AUTH_USER_MODEL = get_user_model()

if hasattr(settings, 'MESSYCMS_BASE_MODEL'):
    ## Developer may define own models if he wants to define additional fields and methods
    Node = plugins.import_module(settings.MESSYCMS_BASE_MODEL)
else:
    class Node(MPTTModel):
        __conf = None
        title = models.CharField(max_length=255, default='', blank=True)
        ## Custom title to show in menu
        menu_title = models.CharField(max_length=255, default='', blank=True)
        slug = models.CharField(max_length=255, default='', blank=True)
        short = models.CharField(max_length=255, default='', blank=True)
        ## Not not using SlugField and not making it unique because it may appear with same name in 
        ## different tree level. Instead we prepare it in self.save().
        type = models.CharField(
            max_length = 255,
            choices = plugins.plugins_list,
            default = plugins.plugins_list[0][0],
            verbose_name = 'Type'
        )
        node_class = models.CharField(max_length=255, default='', blank=True)
        author = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
        group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True)
        timestamp = models.DateTimeField(default=now)
        show_in_menu = models.BooleanField(default=False)
        ## Is node available?
        available = models.BooleanField(default=True)
        content = models.TextField(default='', blank=True)
        parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
        ## Link to tree part, may be used in blocks
        link = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
            help_text='Template node to insert into.', verbose_name='Template')
        sites = models.ManyToManyField(Site, null=True, blank=True)
        
        ## Storage for computed data.
        context = {}
        
        def save(self, *args, **kwargs):
            self.slug = plugins.slugify(self.slug)
            self.node_class = plugins.slugify(self.node_class)
            
            if self.type == '.conf':
                self.slug = self.type
                self.available = False
                self.show_in_menu = False
            elif self.type != 'content' and self.parent_id and self.parent.type != '.conf':
                ## Non "content" types should alwas be children of ".conf" type.
                ## Trying to find conf of parent if exists
                parent_conf = self.parent.get_children().filter(type='.conf').first()
                if not parent_conf:
                    parent_conf = Node.objects.create(type='.conf', parent_id=self.parent_id)
                if parent_conf:
                    self.parent_id = parent_conf.id
            
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
            Node attributes.
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
                        type_name = plugins.slug2name(item.type)
                        if not name:
                            name = plugins.slug2name(type_name)
                        
                        if name:
                            if item.type in self.property_types:
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
                                
                            else:
                                setattr(self.__conf, name, item)
                            
                            if name != type_name:
                                setattr(self.__conf, type_name, getattr(self.__conf, name, None))
                else:
                    self.__conf = ()
                
            return self.__conf
        
        def prop(self, name, default=None):
            '''
            Properties getter. Returns default value if property not exists.
            '''
            return getattr(self.conf, name, default)
        
        def render(self, requestContext):
            '''
            Lazy content rendering, called from template by {% include %} tag
            '''
            return plugins.render(self, requestContext)
        
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
                if 'django.middleware.locale.LocaleMiddleware' in settings.MIDDLEWARE:
                    if slugs[0] in dict(settings.LANGUAGES):
                        ## Throwing away language prefix from url, because
                        ## that middleware prepends it too.
                        del(slugs[0])
            if len(slugs):
                reverse_url = reverse('messycms:node-by-path', kwargs={'path': '/'.join(slugs)})
            else:
                reverse_url = reverse('messycms:root-path')
            
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
                    model = plugins.import_module(model_name)
                else:
                    if self:
                        raise self.DoesNotExist(f'No installed app for model {model_name}')
                    else:
                        raise BaseException(f'No installed app for model {model_name}')
            else:
                model = model_name
            
            return model.objects.get(pk=id)
        
        def is_template_block(self):
            '''
            Bool: is this node for template block?
            '''
            return self.slug.strip('.').startswith('template-block-')
        
        def children_count(self):
            '''
            Real children count, ignores non content type nodes.
            '''
            return self.get_children().filter(type='content').count()
        
        @classmethod
        def get_all_whith_section_type(cls, node_type):
            '''
            Get nodes which have specific section type.
            '''
            result = []
            queryset = cls.objects.filter(type=node_type)
            
            for subnode in queryset:
                if subnode.parent_id:
                    conf = subnode.parent
                    if conf.parent_id and conf.parent.type == 'content' and conf.type == '.conf':
                        if hasattr(conf.parent, 'conf') and hasattr(conf.parent.conf, node_type):
                            if conf.parent.available and conf.parent.author_id and conf.parent.author.is_staff:
                                result.append(conf.parent)
            return result
        
        def __str__(self):
            '''
            Text representation for list in admin interfase
            '''
            if self.slug.startswith('.') or self.type.startswith('.'):
                return self.slug
            else:
                return '%s: %s' % (self.id, self.title or self.menu_title or self.short or self.slug)
        
        ## Types used as property
        property_types = ('.property', '.redirect')
        
        ## Fields visibility in admin.
        fields_toggle = {
            '.property': (
                {'field': 'slug', 'label': 'Property name'},
                {'field': 'short', 'label': 'Short value'},
                {'field': 'content', 'label': 'Long Value', 'help': 'JSON allowed. If empty, "short value" will be used.'},
                'parent',
                'type',
                'id',
            ),
            '.redirect': (
                {'field': 'short', 'label': 'Redirect to URL'},
                {'field': 'link', 'label': 'Redirect to node'},
                'parent',
                'type',
                'id',
            ),
            'inclusion_point': (
                {'field': 'slug', 'label': 'Alias'},
                'parent',
                'type',
                'id',
            ),
           '.conf': (
                'type',
                'parent',
                'id',
            ),
        }

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