import sys, os
from django.template.loader import render_to_string as dj_render_to_string
from django.template import TemplateDoesNotExist, Template, Context
from django.utils import text
from django.utils.safestring import mark_safe
from django.conf import settings
from django.urls import resolve

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
        ('.conf', 'Node conf'),
        ('inclusion_point', 'Inclusion point'),
        ('render_view', 'Render view'),
    )

def render(node, request):
    if not hasattr(request, 'CACHE'):
        setattr(request, 'CACHE', {})
    if 'rendered' not in request.CACHE:
        request.CACHE['rendered'] = {}
    
    if node.id in request.CACHE['rendered']:
        ## already processed
        node.content = request.CACHE['rendered'][node.id].content
        return node
    request.CACHE['rendered'][node.id] = node
    
    if node.type.startswith('.'):
        ## It's service type
        node.content = ''
        return node
    
    available_plugins = dict(get_list())
    
    inclusion_point_string = ''
    if node.link_id and node.link_id not in request.CACHE['rendered'] and node.type == 'content':
        ## Using node.link as parent template.
        ## We insert current node content into it in the end of this function.
        
        ## Rendering parent template
        render(node.link, request)
        inclusion_point_string = inclusion_point(node.link, request)['content']
    
    
    if node.type in available_plugins: # {
        node.content += f'<!-- block {node.id} -->\n'
        
        ## If there is method
        #if node.type in dir():
        if hasattr(self, node.type): ## same as above {
            ## Calling method from this module
            result = getattr(self, node.type)(node, request)
            if result: # {
                #if 'nodes' in result:
                #    for _ in result['nodes']:
                #        render_node(_, request)
                
                if 'templates' in result:
                    node.content += render_to_string(
                        result['templates'],
                        getattr(node.conf, 'template', ''),
                        node.context,
                        request
                    )
                
                if 'content' in result:
                    node.content += result['content']
            # } endif result
        # } ## endif there is method
        else: # {
            ## If current node is a section for some node
            if node.parent_id and node.parent.type == '.conf' and node.author.is_staff:
                ## This will add a section to owning node using slug as template
                ## name and rendered with parent context
                node.content = render_to_string(
                    templates(node, request),
                    node.content,
                    {'node': request.CACHE['rendered'].get(node.parent.parent_id, node.parent.parent)},
                    request
                )
        # }
        
        node.content += f'<!-- endblock {node.id} -->\n'
        
        ## Now rendering included nodes if exist
        for block in node.conf:
            node.content += render(block, request).content
    # } endif plugin available
    
    if inclusion_point_string and inclusion_point_string in node.link.content:
        ## Inserting current node content into parent template node and replacing this with that.
        node.content = node.link.content.replace(inclusion_point_string, node.content)
    
    if node.author.is_staff:
        node.content = mark_safe(node.content)
    return node

def templates(block, request=None):
    templatedir = 'messycms/blocks'
    
    ## So, we can get three templates:
    ##     type-class-item.html
    ##     type-class.html
    ##     type.html
    
    block_type = slugify(block.type)
    template_name = slugify(getattr(block.conf, 'template', ''))
    
    templates = [
        os.path.join(templatedir, f'{block_type}-{template_name}.html'),
        os.path.join(templatedir, f'{template_name}.html'),
        os.path.join(templatedir, f'{block_type}-{slugify(block.title)}.html'),
        os.path.join(templatedir, f'{block_type}-{slugify(block.slug)}.html'),
        os.path.join(templatedir, f'{block_type}-{slugify(block.short)}.html'),
        os.path.join(templatedir, f'{slugify(block.slug)}.html'),
        os.path.join(templatedir, f'{block_type}.html'),
    ]
    
    if request and hasattr(request, 'site'):
        ## Also adding variants for current domain
        ## e.g. domain/messcms/blocks/
        for path in reversed(templates[:]):
            templates.insert(0, os.path.join(request.site.domain, templatedir, path))
    
    return templates

def render_to_string (templates=[], template='', context={}, request=None):
    '''
    Renders template to string.
    If `template` is not empty, using it as string template, else using
    `templates` list as file based templates.
    Other attrs:
        `context`, `request`
    '''
    result = ''
    if template:
        tpl = Template(template)
        result = tpl.render(Context(context))
    
    if templates:
        try:
            result += dj_render_to_string(templates, context, request)
        except TemplateDoesNotExist:
            pass
    
    return result

## This module contains some basic plugins.
## Additional plugins may be placed inside this module dirs.
## Also project may define it's own plugins (TODO not implemented)

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

def inclusion_point(node, request, *args, **kwargs):
    if node.type == 'inclusion_point':
        id = node.parent.parent.id
    else:
        id = node.id
    
    return {'content': f'<template data-id="{id}"></template>'}

def render_view(node, request, *args, **kwargs):
    if node.short:
        resolved = resolve(node.short)
        response = resolved.func(request, **resolved.kwargs)
        node.content += response.content.decode(response.charset)
    return {}
