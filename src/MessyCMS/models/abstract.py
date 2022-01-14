from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
#from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from mptt.models import MPTTModel, TreeForeignKey
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from MessyCMS import plugins
import json

settings.CACHE_TIMESTAMP = timezone.now().timestamp()

AUTH_USER_MODEL = get_user_model()

class MessyBase(MPTTModel):
    class Meta:
        abstract = True
    
    __conf = None
    __rendered = ''
    
    ## Node type
    type = models.CharField(
        max_length = 255,
        choices = plugins.plugins_list,
        default = plugins.plugins_list[0][0],
        verbose_name = 'Type'
    )
    title = models.CharField(max_length=255, default='', blank=True)
    ## Custom title to show in menu
    menu_title = models.CharField(max_length=255, default='', blank=True)
    slug = models.CharField(max_length=255, default='', blank=True)
    short = models.CharField(max_length=255, default='', blank=True)
    ## Not not using SlugField and not making it unique because it may appear with same name in 
    ## different tree level. Instead we prepare it in self.save().
    node_class = models.CharField(max_length=255, default='', blank=True)
    author = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True)
    show_in_menu = models.BooleanField(default=False)
    ## Is node available?
    available = models.BooleanField(default=True)
    content = models.TextField(default='', blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    ## Link to tree part, may be used in blocks
    link = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
        help_text='Template node to insert into.', verbose_name='Parent template')
    sites = models.ManyToManyField(Site, null=True, blank=True)
    ts_created = models.DateTimeField(default=timezone.now)
    ts_updated = models.DateTimeField(auto_now=True)
    
    ## Storage for computed data.
    context = {}
    
    def save(self, *args, **kwargs):
        self.slug = plugins.slugify(self.slug)
        self.node_class = plugins.slugify(self.node_class)
        
        if self.type == '.conf':
            self.slug = self.type
            self.available = False
            self.show_in_menu = False
        elif self.parent_id and self.parent.type != '.conf':
            if self.type != 'content' or self.context.get('saveasproperty', None):
                ## Non "content" types should alwas be children of ".conf" type.
                ## Trying to find conf of parent if exists
                parent_conf = self.parent.get_children().filter(type='.conf').first()
                if not parent_conf:
                    parent_conf = plugins.get_model().objects.create(type='.conf', parent_id=self.parent_id)
                if parent_conf:
                    self.parent_id = parent_conf.id
        
        super().save(*args, **kwargs)
        settings.CACHE_TIMESTAMP = timezone.now().timestamp()
    
    @property
    def conf(self):
        '''
        Node attributes.
        '''
        if not self.__conf:
            #self.__conf = self.get_children().filter(type='.conf').first()
            ## For some strange reason above method sometimes returns None
            ## when this function is invoked from template.
            self.__conf = plugins.get_model().objects.filter(parent_id=self.id, type='.conf').first()
            
            if self.__conf:
                self.__conf = self.__conf.get_children()
                for item in self.__conf:
                    ## Preparing content properties
                    name = ''
                    if item.property_field_allowed('slug'):
                        name = plugins.slug2name(item.slug)
                    type_name = plugins.slug2name(item.type)
                    if not name:
                        name = type_name
                    
                    if name:
                        if item.type in self.property_types:
                            value = ''
                            
                            if item.property_field_allowed('content'):
                                value = item.content.strip()
                            
                            if not value and item.property_field_allowed('short'):
                                value = item.short.strip()
                            
                            if value:
                                if '=' in value:
                                    parsed_model = value.split('=')
                                    try:
                                        value = self.get_from_model(parsed_model[0], parsed_model[1])
                                    except:
                                        pass
                                
                                if (type(value) is str):
                                    ## Try interpret value as JSON
                                    try:
                                        value = json.loads(value)
                                    except:
                                        pass
                                
                                setattr(self.__conf, name, value)
                            elif item.link_id and item.property_field_allowed('link'):
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
    
    def render(self, requestContext, *args, **kwargs):
        '''
        Lazy content rendering, called from template by {% include %} tag
        '''
        
        node_was_cached = 'allnodes' in requestContext and self.id in requestContext['allnodes']
        
        if not self.__rendered:
            self.__rendered = plugins.render(self, requestContext)
        
        if self.append_to() and not node_was_cached:
            ## If node rendering should be deferred
            return ''
        else:
            return self.__rendered
    
    def get_node_path(self):
        ancestors = self.get_ancestors(include_self=True).values()
        slugs = []
        for item in ancestors:
            ## Skipping root directory because it used for site root.
            if item['parent_id']:
                slug = item['slug']
                
                if not slug:
                    slug = item['id']
                
                slugs.append(slugify(slug, allow_unicode=True))
        return slugs
    
    def get_absolute_url(self):
        '''
            Builds URL path of item.
        '''
        slugs = self.get_node_path()
        
        lang_node = ''
        
        if len(slugs):
            if 'django.middleware.locale.LocaleMiddleware' in settings.MIDDLEWARE:
                if slugs[0] in dict(settings.LANGUAGES):
                    ## Throwing away language prefix from url, because
                    ## that middleware prepends it too.
                    lang_node = slugs[0]
                    del(slugs[0])
        
        if len(slugs):
            reverse_url = reverse('messycms:node-by-path', kwargs={'path': '/'.join(slugs)})
        else:
            reverse_url = reverse('messycms:root-path')
        
        if lang_node:
            ## LocaleMiddleware prepends current language to url.
            ## But we need actual language of node.
            l_reverse_url = reverse_url.split('/')
            l_reverse_url[1] = lang_node
            reverse_url = '/'.join(l_reverse_url)
        
        return reverse_url
    
    def get_from_model(self, model_name, id=0):
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
        
        if id:
            result = model.objects.get(pk=id)
        else:
            result = model.objects.all()
        return result
    
    def append_to(self):
        '''
        If this node is for appending to particular HTML element, return that HTML element name
        '''
        append_to = ''
        stripped_slug = self.slug.strip('.')
        if stripped_slug.startswith('append-to-'):
            append_to = stripped_slug.replace('append-to-', '')
            append_to = f'</{append_to}>'
        return append_to
        #return append_to.encode('utf-8') ## bytes
    
    def children_count(self):
        '''
        Real children count, ignores non content type nodes.
        '''
        return self.get_children().filter(available=True, type='content').count()
    
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
            return self.slug or self.type
        else:
            return '%s: %s' % (self.id, self.title or self.menu_title or self.short or self.slug or self.type)
    
    ## Types used as property
    property_types = ('.property', '.redirect', '.modelItem', '.ext-template')
    
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
        '.ext-template': (
            {'field': 'link', 'label': 'External template node', 'help': 'Select node to use as template for rendering this node.'},
            'parent',
            'type',
            'id',
        ),
        '.modelItem': (
            {'field': 'slug', 'label': 'Property name'},
            {'field': 'short', 'label': 'Value', 'help': 'Value format: app.model=id'},
            #{'field': 'content', 'label': 'Long Value', 'help': 'JSON allowed. If empty, "short value" will be used.'},
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
    
    def property_field_allowed(self, field):
        '''If field is allowed for this node of type property.'''
        result = False
        if self.type in self.fields_toggle:
            fields = tuple(filter(lambda x: (type(x) is dict and x['field'] == field) or x == 'field', self.fields_toggle[self.type]))
            result = len(fields) > 0
        return result
    
    def get_stored_template(self):
        template = ''
        ext_template = self.prop('extTemplate')
        
        if type(ext_template) is type(self) and ext_template.content:
            template = ext_template.content
        if not template:
            template = self.prop('template')
        if not template and self.link_id and self.link.type == 'content':
            template = self.link.content
        if not template:
            template = self.content
        
        return template
