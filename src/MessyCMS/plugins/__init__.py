import sys, os
from django.template.loader import render_to_string as dj_render_to_string
from django.template import TemplateDoesNotExist, Template, Context
from django.utils import text
from django.utils.safestring import mark_safe
from django.conf import settings
from django.urls import resolve

## This module contains some basic plugins.
## Additional plugins may be placed inside this module dirs.
## Also project may define it's own plugins (TODO not implemented)

self = sys.modules[__name__]
DEBUG = False #settings.DEBUG

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

def get_list():
    ## TODO add support of project local plugins
    return (
        ('content', 'Content'),
        ('items_tree', 'Items tree'),
        ('items_list', 'Items list'),
        ('include_item', 'Inclue item'),
        ('.property', 'Property'),
        ('.conf', 'Node config directory'),
        ('inclusion_point', 'Inclusion point'),
        ('render_view', 'Render view'),
    )

def render(node, requestContext):
    if node.type.startswith('.'):
        ## It's service type
        return ''
    
    available_plugins = dict(get_list())
    
    rendered_string = ''
    if settings.DEBUG:
        rendered_string = f'<!-- block id: {node.id}; type: {node.type} -->\n'
    
    if node.type in available_plugins: # {
        ## If there is method
        #if node.type in dir():
        if hasattr(self, node.type): ## same as above {
            #rendered_string += node.content
            ## Calling method from this module
            result = getattr(self, node.type)(node, requestContext.request)
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
            if node.parent_id and node.parent.type == '.conf' and node.author.is_staff:
                ## This will add a section to owning node using slug as template
                ## name and rendered with parent context
                rendered_string += render_to_string(
                    templates(node, requestContext.request),
                    node.content,
                    {'node': node.parent.parent},
                    requestContext.request
                )
            elif node.author.is_staff:
                node.content = mark_safe(node.content)
                rendered_string += render_to_string(
                    templates(node, requestContext.request),
                    node.content,
                    {'node': node},
                    requestContext.request
                )
            else:
                rendered_string += node.content
        ## }
    
    ## endif type in available_plugins }
    #else: # {
    #    ## No plugins for this type of node
    #    if node.author.is_staff:
    #        ## If author is staff we try to use content as template
    #        rendered_string += render_to_string(
    #            templates(node, requestContext.request),
    #            node.content,
    #            {'node': node, 'parentContext': requestContext},
    #            requestContext.request
    #        )
    #    else:
    #        rendered_string += node.content
    ## endif }
    
    if settings.DEBUG:
        rendered_string += f'\n<!-- endblock {node.id} -->\n'
    
    return rendered_string

def templates(block, request=None):
    templatedir = 'messycms/blocks'
    
    ## So, we can get three templates:
    ##     type-class-item.html
    ##     type-class.html
    ##     type.html
    
    block_type = slugify(block.type).strip('.')
    template_name = slugify(getattr(block.conf, 'template', '')).strip('.')
    block_title = slugify(block.title).strip('.')
    block_slug = slugify(block.slug).strip('.')
    block_short = slugify(block.short).strip('.')
    block_class = slugify(block.node_class).strip('.')
    
    templates = [
        os.path.join(templatedir, f'{block_type}-{template_name}.html'),
        os.path.join(templatedir, f'{template_name}.html'),
        os.path.join(templatedir, f'{block_type}-{block_title}.html'),
        os.path.join(templatedir, f'{block_type}-{block_slug}.html'),
        os.path.join(templatedir, f'{block_type}-{block_short}.html'),
        os.path.join(templatedir, f'{block_type}-{block_class}.html'),
        os.path.join(templatedir, f'{block_slug}.html'),
        os.path.join(templatedir, f'{block_class}.html'),
        os.path.join(templatedir, f'{block_type}.html'),
    ]
    
    if request and hasattr(request, 'site'):
        ## Also adding variants for current domain
        ## e.g. domain/messcms/blocks/
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

def items_tree(block, request=None, *args, **kwargs):
    '''
    Renders tree type block. TODO add menu support
    '''
    result = {}
    if block.link:
        items = block.link.get_descendants().filter(available=True, *args, **kwargs)
        if items:
            result = {
                'templates': templates(block, request),
                'context': {
                    'nodes': items,
                    'node': block
                }
            }
            block.context.update(result['context'])
    return result

def items_list(block, request=None, *args, **kwargs):
    '''
    Renders one level list of items.
    '''
    result = {}
    items = None
    if block.link:
        items = block.link.get_children().filter(available=True)
    else:
        ## Using parent if no link defined
        items = block.parent.parent.get_children().filter(available=True)
    
    ## If block has "sort" property
    sort = block.prop('sort')
    if sort:
        if type(sort) is list:
            items = items.order_by(*sort)
        else:
            items = items.order_by(sort)
    
    ## If block has "limit" property
    limit = block.prop('limit')
    ## If block has "pagination" property
    ## Should contain number of items per page
    pagination = int(block.prop('pagination', 0))
    
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
            'templates': templates(block, request),
            'context': {
                'nodes': items,
                'node': block
            }
        }
        block.context.update(result['context'])
    
    return result

def include_item(block, request=None, *args, **kwargs):
    '''
    Renders one element.
    '''
    result = {}
    if block.link and block.link.available:
        result = {
            'templates': templates(block, request),
            'context': {
                'nodes': [block.link],
                'node': block
            }
        }
        block.context.update(result['context'])
    return result

def render_view(node, request, *args, **kwargs):
    if node.short:
        resolved = resolve(node.short)
        response = resolved.func(request, **resolved.kwargs)
        node.content += response.content.decode(response.charset)
    return {}
