import sys, os
from django.template.loader import render_to_string
from django.utils import text
from django.utils.safestring import mark_safe
from django.conf import settings

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
    Turns string 'aaa-bbb-ccc' into 'AaaBbbCcc'
    '''
    
    parts = slug.split('-')
    parts = [ x.capitalize() if x != parts[0] else x for x in parts]
    return ''.join(parts).strip('.- ')

def get_list():
    ## TODO add support of project local plugins
    return (
        ('html', 'HTML'),
        ('items_tree', 'Items tree'),
        ('items_list', 'Items list'),
        ('include_item', 'Inclue item'),
        ('.property', 'Property'),
        ('.pageconf', 'Page conf'),
        ('inclusion_point', 'Inclusion point'),
    )


def render_node(node, request=None, ready_blocks=None):
    if ready_blocks is None:
        ready_blocks = {}
    
    if node.fmt.startswith('.'):
        ## It's service type
        node.content = ''
        return node
    
    if node.id in ready_blocks:
        ## already processed
        node.content = ready_blocks[node.id].content
        return node
    ready_blocks[node.id] = node
    
    available_plugins = dict(get_list())
    
    if node.fmt in available_plugins: # {
        node.content += f'<!-- block {node.id} -->\n'
        
        #if node.fmt in dir():
        if hasattr(self, node.fmt): ## same as above
            ## Calling method from this module
            result = getattr(self, node.fmt)(node, request)
            if result: # {
                if 'nodes' in result:
                    for _ in result['nodes']:
                        render_node(_, request, ready_blocks)
                
                if 'templates' in result:
                    node.content += render_to_string(
                        result['templates'],
                        {
                            ## Tree nodes
                            'nodes': result['nodes'],
                            ## Page self
                            'page': node
                        },
                        request
                    )
                
                if 'content' in result:
                    node.content += result['content']
            # } endif result
        node.content += f'<!-- endblock {node.id} -->\n'
        
        ## Now rendering included nodes if exist
        for block in node.pageconf:
            node.content += render_node(block, request, ready_blocks).content
    # } endif plugin available
    
    if node.link_id and node.fmt == 'html':
        ## Using node.link as parent template.
        ## We insert current node content into it.
        
        ## Rendering parent template
        render_node(node.link, request, ready_blocks)
        inclusion_point_string = inclusion_point(node.link, request)['content']
        if inclusion_point_string in node.link.content:
            node.content = node.link.content.replace(inclusion_point_string, node.content)
    
    ## TODO make it only if author is in staff group
    node.content = mark_safe(node.content)
    
    return node

def templates(block):
    templatedir = 'messcms/blocks'
    
    ## So, we can get three templates:
    ##     type-class-item.html
    ##     type-class.html
    ##     type.html
    
    block_type = slugify(block.fmt)
    
    return (
        os.path.join(templatedir, f'{block_type}-{slugify(block.title)}.html'),
        os.path.join(templatedir, f'{block_type}-{slugify(block.slug)}.html'),
        os.path.join(templatedir, f'{block_type}-{slugify(block.short)}.html'),
        #os.path.join(templatedir, f'{block_type}-test.html'),
        os.path.join(templatedir, f'{block_type}.html'),
    )

## This module contains some basic plugins.
## Additional plugins may be placed inside this module dirs.
## Also project may define it's own plugins (TODO not implemented)

def items_tree(block, request=None, *args, **kwargs):
    '''
    Renders tree type block. TODO add menu support
    '''
    result = None
    if block.link:
        items = block.link.get_descendants().filter(available=True, *args, **kwargs)
        if items:
            result = {'templates': templates(block), 'nodes': items}
    return result

def items_list(block, request=None, *args, **kwargs):
    '''
    Renders one level list of items.
    '''
    result = None
    items = None
    if block.link:
        items = block.link.get_children().filter(available=True)
    else:
        items = block.parent.parent.get_children().filter(available=True)
    
    if items:
        result = {'templates': templates(block), 'nodes': items}
    
    return result

def include_item(block, request=None, *args, **kwargs):
    '''
    Renders one element.
    '''
    result = None
    if block.link and block.link.available:
        result = {'templates': templates(block), 'nodes': [block.link]}
    return result

def inclusion_point(node, request, *args, **kwargs):
    if node.fmt == 'inclusion_point':
        id = node.parent.parent.id
    else:
        id = node.id
    
    return {'content': f'<template data-id="{id}"></template>'}
