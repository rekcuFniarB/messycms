import sys, os
import re
from django.template.loader import render_to_string as dj_render_to_string
from django.template import TemplateDoesNotExist, Template, Context
from django.utils import text
from django.utils.safestring import mark_safe
from django.conf import settings
from django.urls import resolve
from django.http import HttpResponseRedirect
import importlib
#from ..models import Node ## this produces "app not ready yet" error.

## This module contains some basic plugins.
## Also project may define its own plugins.

self = sys.modules[__name__]
DEBUG = False #settings.DEBUG

__IMPORTED_MODULES__ = {}
__PLUGIN_INSTANCES__ = {}

regexp = {
    'ahref': re.compile(r'<a\s+href="(/\d+?/)"'),
    'digit': re.compile(r'\d+')
}

class MessyPlugin:
    def execute(self, node, request=None, *args, **kwargs):
        '''
        Main plugin method.
        node: model instance
        request: request
        Returns dict
        '''
        return {
            'templates': templates(node, request),
            'context': {
                'nodes': [node],
                'node': node
            },
            'content': ''
        }
    
    fields_toggle = (
        ## define which fields to show in admin
        #{'field': 'title', 'label': 'Title', 'help': 'Optional field description'},
        ## Or just field name
        #'node_class',
    )

def import_module(name):
    '''
    Imports class from module and returns it. Name is string in the form of "module.classname"
    '''
    if name not in __IMPORTED_MODULES__:
        _name = name.split('.')
        if len(_name) > 1:
            ## Expected value of "name" is "module.className"
            class_name = _name.pop()
            module_name = '.'.join(_name)
            __IMPORTED_MODULES__[name] = getattr(importlib.import_module(module_name), class_name)
        else:
            __IMPORTED_MODULES__[name] = importlib.import_module(name)
    return __IMPORTED_MODULES__[name]

def get_model():
    ## Lazy model getter to workaround "app not ready error"
    if not getattr(self, 'NodeModel', None):
        from ..models import Node
        setattr(self, 'NodeModel', Node)
    return NodeModel

def slugify(slug, *args, **kwargs):
    '''
    django.utils.text.slugify() wrapper.
    It preserves leading dot and replaces "_" with "-"
    '''
    start = ''
    if slug.startswith('.'):
        start = '.'
    return start + text.slugify(slug.replace('_', '-'), *args, **kwargs)

def slug2name(slug):
    '''
    Turns string 'aaa-bbb-ccc' into 'aaaBbbCcc'
    '''
    
    parts = slug.split('-')
    parts = [ x.capitalize() if x != parts[0] else x for x in parts]
    return ''.join(parts).strip('.- ')

## List of defined plugins
plugins_list = [
        ('content', 'Content'),
        ('ItemsTree', 'Items tree'),
        ('ItemsList', 'Items list'),
        ('IncludeItem', 'Inclue item'),
        ('.property', 'Property'),
        ('.redirect', 'Redirect'),
        ('.conf', 'Node config directory'),
        ('inclusion_point', 'Inclusion point'),
        ('RenderView', 'Render view'),
    ] + getattr(settings, 'MESSYCMS_PLUGINS', [])


def get_plugin_instance(name):
    '''
    Load once and return plugin
    '''
    if name not in __PLUGIN_INSTANCES__:
        plugin_class = getattr(self, name, None)
        if not plugin_class:
            try:
                plugin_class = import_module(name)
            except (ModuleNotFoundError, ValueError):
                plugin_class = lambda: None
        __PLUGIN_INSTANCES__[name] = plugin_class()
    return __PLUGIN_INSTANCES__[name]

def render(node, requestContext):
    if node.type.startswith('.'):
        ## It's service type
        return ''
    
    available_plugins = dict(plugins_list)
    
    rendered_string = ''
    if settings.DEBUG:
        rendered_string = f'<!-- block id: {node.id}; type: {node.type} -->\n'
    
    if node.type in available_plugins and node.author_id and node.author.is_staff: # {
        ## If there is method
        #if node.type in dir():
        plugin_instance = get_plugin_instance(node.type)
        
        if plugin_instance: ## same as above {
            ## Calling method from this module
            result = plugin_instance.execute(node, requestContext.request)
            if result: # {
                rendered_string += render_to_string(
                    ## file based list of templates to try
                    result.get('templates', ()),
                    ## db based template
                    getattr(node.conf, 'template', node.content),
                    result.get('context', node.context),
                    requestContext.request
                )
                
                #if 'content' in result:
                    #rendered_string += result['content']
            ## } endif result
        ## }  endif there is plugin method
        else: ## { No method for this node type
            ## If current node is a section of some node
            if node.parent_id and node.parent.type == '.conf':
                ## This will add a section to owning node using slug as template
                ## name and rendered with parent context
                rendered_string += render_to_string(
                    templates(node, requestContext.request),
                    node.content,
                    {'node': node.parent.parent},
                    requestContext.request
                )
            else:
                node.content = mark_safe(node.content)
                rendered_string += render_to_string(
                    templates(node, requestContext.request),
                    node.content,
                    {'node': node},
                    requestContext.request
                )
        ## }
    
    ## } endif type in available_plugins
    else: ## {
        ## No plugin for this type of node or node author is not staff
        rendered_string += node.content
    ## endif }
    
    if settings.DEBUG:
        rendered_string += f'\n<!-- endblock {node.id} -->\n'
    
    rendered_string = parse_links(rendered_string)
    
    return rendered_string

def parse_links(string):
    '''
    Resolving local redirecting links to actual urls.
    '''
    for match in regexp['ahref'].finditer(string):
        try:
            resolved = resolve(match[1])
            if resolved.url_name == 'messycms-node-by-id' and 'id' in resolved.kwargs:
                node = get_model().objects.get(pk=resolved.kwargs['id'])
                if node:
                    replacement = match[0].replace(match[1], node.get_absolute_url())
                    string = string.replace(match[0], replacement)
        except:
            pass
    return string

def templates(node, request=None):
    templatedir = 'messycms/blocks'
    
    ## So, we can get three templates:
    ##     type-class-item.html
    ##     type-class.html
    ##     type.html
    
    node_type = slugify(node.type).strip('.')
    template_name = slugify(getattr(node.conf, 'template', '')).strip('.')
    node_title = slugify(node.title).strip('.')
    node_slug = slugify(node.slug).strip('.')
    node_short = slugify(node.short).strip('.')
    node_class = slugify(node.node_class).strip('.')
    
    templates = [
        os.path.join(templatedir, f'{node_type}-{template_name}.html'),
        os.path.join(templatedir, f'{template_name}.html'),
        os.path.join(templatedir, f'{node_type}-{node_title}.html'),
        os.path.join(templatedir, f'{node_type}-{node_slug}.html'),
        os.path.join(templatedir, f'{node_type}-{node_short}.html'),
        os.path.join(templatedir, f'{node_type}-{node_class}.html'),
        os.path.join(templatedir, f'{node_slug}.html'),
        os.path.join(templatedir, f'{node_class}.html'),
        os.path.join(templatedir, f'{node_type}.html'),
    ]
    
    if request and hasattr(request, 'site'):
        ## Also adding variants for current domain
        ## e.g. domain/messcms/nodes/
        for path in reversed(templates[:]):
            templates.insert(0, os.path.join(request.site.domain, path))
    
    return templates

def render_to_string(templates=[], template='', context={}, request=None):
    '''
    Renders template to string.
    If `template` is not empty, using it as string template, else using
    `templates` list as file based templates.
    Other attrs:
        `context`, `request`
    '''
    
    result = ''
    
    if template:
        try:
            tpl = Template(template)
            db_tpl_render = tpl.render(Context(context))
            if db_tpl_render != template:
                ## if not equal, it means that it contained a template code.
                result = db_tpl_render
        except:
            if settings.DEBUG:
                raise
    
    if not result and templates:
        try:
            result = dj_render_to_string(templates, context, request)
        except TemplateDoesNotExist:
            pass ## just ignoring, it's ok if template file is not defined.
    
    if not result:
        result = template
    
    return result

class ItemsTree(MessyPlugin):
    '''
    Renders tree type node.
    '''
    def execute(self, node, request=None, *args, **kwargs):
        result = {}
        if node.link:
            items = node.link.get_descendants().filter(available=True, type='content', *args, **kwargs)
            if items:
                result = {
                    'templates': templates(node, request),
                    'context': {
                        'nodes': items,
                        'node': node
                    }
                }
                node.context.update(result['context'])
        
        return result
    
    fields_toggle = (
        {'field': 'slug', 'label': 'Alias'},
        {'field': 'title', 'label': 'Title'},
        'node_class',
        'available',
        {'field': 'content', 'label': 'Content / Template'},
        'parent',
        {'field': 'link', 'label': 'Source', 'help': 'Select node to use as data source. Parent node used if empty.'},
        'type',
        'id',
    )

class ItemsList(ItemsTree):
    def execute(self, node, request=None, *args, **kwargs):
        result = {}
        if node.link:
            items = node.link.get_children().filter(available=True)
        else:
            ## Using parent if no link defined
            items = node.parent.parent.get_children().filter(available=True, type='content')
        
        ## If node has "sort" property
        sort = node.prop('sort')
        if sort:
            if type(sort) is list:
                items = items.order_by(*sort)
            else:
                items = items.order_by(sort)
        
        ## If node has "limit" property
        limit = node.prop('limit')
        ## If node has "pagination" property
        ## Should contain number of items per page
        pagination = int(node.prop('pagination', 0))
        
        if pagination:
            from django.core.paginator import Paginator
            paginator = Paginator(items, pagination)
            items = paginator.get_page(request.GET.get('page'))
        elif limit:
            if type(limit) is list:
                if len(limit) > 1:
                    items = items[limit[0]:limit[1]]
                else:
                    items = items[:limit[0]]
            else:
                items = items[:int(limit)]
        
        if items:
            result = {
                'templates': templates(node, request),
                'context': {
                    'nodes': items,
                    'node': node
                }
            }
            node.context.update(result['context'])
        
        return result

class IncludeItem(ItemsTree):
    '''
    Renders one element.
    '''
    def execute(self, node, request=None, *args, **kwargs):
        result = {}
        if node.link and node.link.available:
            result = {
                'templates': templates(node, request),
                'context': {
                    'nodes': [node.link],
                    'node': node
                }
            }
            node.context.update(result['context'])
        return result

class RenderView(MessyPlugin):
    def execute(self, node, request, *args, **kwargs):
        if node.short:
            resolved = resolve(node.short)
            response = resolved.func(request, **resolved.kwargs)
            node.content += response.content.decode(response.charset)
        return {'templates': templates(node, request)}
    
    fields_toggle = (
        {'field': 'slug', 'label': 'Alias'},
        {'field': 'short', 'label': 'View URL from urlconf'},
        'parent',
        'available',
        'type',
        'id',
    )
