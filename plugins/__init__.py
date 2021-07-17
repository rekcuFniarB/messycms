import sys, os
from django.shortcuts import render as render_template
from django.utils.text import slugify as django_slugify

self = sys.modules[__name__]

def slugify(text):
    return django_slugify(text.replace('_', '-'))

def get_list():
    ## TODO add support of project local plugins
    return (
        ('html', 'HTML'),
        ('items_tree', 'Items tree'),
        ('items_list', 'Items list'),
        ('include_item', 'Inclue item'),
    )

def render(request, page):
    '''
    Renders each page block.
    '''
    if not page.pageconf():
        return page.content
    
    blocks = page.pageconf().get_children()
    available_plugins = dict(get_list())
    for block in blocks:
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

def items_tree(block):
    '''
    Renders menu type block
    '''
    result = None
    if block.link:
        items = block.link.get_descendants().filter(show_in_menu=True, available=True)
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
