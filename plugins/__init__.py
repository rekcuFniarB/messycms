import sys, os
from django.shortcuts import render as render_template
from django.utils import text

self = sys.modules[__name__]

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
    return ''.join(parts).strip('. ')

def get_list():
    ## TODO add support of project local plugins
    return (
        ('html', 'HTML'),
        ('items_tree', 'Items tree'),
        ('items_list', 'Items list'),
        ('include_item', 'Inclue item'),
        ('property', 'Property'),
    )

def render(request, page):
    '''
    Renders each page block.
    '''
    #if not page.pageconf():
        #return page.content
    
    #blocks = page.pageconf().get_children()
    available_plugins = dict(get_list())
    for block in page.pageconf():
        if block.fmt in available_plugins:
            page.content += f'<!-- block {block.fmt} -->\n'
            if block.fmt == 'html':
                page.content += block.content
            ## If function exists here
            #elif block.fmt in dir():
            elif hasattr(self, block.fmt): ## same as above
                ## calling function named as block.fmt
                result = getattr(self, block.fmt)(block)
                if result:
                    page.content += render_template(
                        request, result['templates'],
                        {
                            ## Menu tree nodes
                            'nodes': result['nodes'],
                            ## Page self
                            'page': page
                        }
                    ).content.decode('utf-8')
            page.content += f'<!-- endblock {block.fmt} -->\n'
    return page.content

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
        os.path.join(templatedir, f'{block_type}.html'),
    )

## This module contains some basic plugins.
## Additional plugins may be placed inside this module dirs.
## Also project may define it's own plugins (TODO not implemented)

def items_tree(block, show_in_menu=False):
    '''
    Renders menu type block
    '''
    result = None
    if block.link:
        items = block.link.get_descendants().filter(show_in_menu=show_in_menu, available=True)
        if items:
            result = {'templates': templates(block), 'nodes': items}
    return result

def items_list(block):
    '''
    Renders list of items
    '''
    result = None
    if block.link:
        items = block.link.get_children().filter(available=True)
        if items:
            result = {'templates': templates(block), 'nodes': items}
    return result

def include_item(block):
    '''
    Renders one element
    '''
    result = None
    if block.link and block.link.available:
        result = {'templates': templates(block), 'nodes': block.link}
    return result
