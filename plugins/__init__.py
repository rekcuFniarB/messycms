import sys, os
from django.shortcuts import render as render_template
from django.utils import text
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
    )


def render_node(node, request=None, ready_blocks=None, parent=None):
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
    
    if DEBUG:
        node.content += f'<h3>Block {parent}/{node.id} / {node.slug} / {node.fmt}'
    
    
    if node.fmt in available_plugins: # {
        node.content += f'<!-- block {node.id} / {node.slug} / {node.fmt} -->\n'
        
        #if node.fmt in dir():
        if hasattr(self, node.fmt): ## same as above
            ## Calling method from this module
            result = getattr(self, node.fmt)(node)
            if result: # {
                for _ in result['nodes']:
                    render_node(_, request, ready_blocks, node.id)
                
                node.content += render_template(
                    request, result['templates'],
                    {
                        ## Tree nodes
                        'nodes': result['nodes'],
                        ## Page self
                        'page': node
                    }
                ).content.decode('utf-8')
            # } endif result
        node.content += f'<!-- endblock {node.id} / {node.slug} / {node.fmt} -->\n'
        
        #print('NODE CONF:', node.pageconf)
        
        if DEBUG:
            node.content += f'<h4>BEGIN SUBBLOCKS {parent}/{node.id}</h4>\n'
        ## Now rendering included nodes if exist
        for block in node.pageconf:
            print('SUB BLOCK:', block)
            node.content += render_node(block, request, ready_blocks, node.id).content
            if (block.fmt == 'html'):
                print('HTML', block.content)
                #node.content += block.content
            #node.content += block.content
            if DEBUG:
                node.content += f'<h4>SUBBLOCK {parent}/{node.id}/{block.id}</h4>\n'
        if DEBUG:
            node.content += f'<h4>END SUBBLOCKS {parent}/{node.id}</h4>\n'
        
        
    # } endif plugin available
    else:
        node.content += f'<b>NONE</b><!-- noplug {node.id} / {node.slug} / {node.fmt} -->\n'
    
    if DEBUG:
        node.content += f'<h3>EndBlock {parent}/{node.id} / {node.slug} / {node.fmt}'
    
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

def items_tree(block, *args, **kwargs):
    '''
    Renders tree type block. TODO add menu support
    '''
    result = None
    if block.link:
        items = block.link.get_descendants().filter(available=True, *args, **kwargs)
        if items:
            result = {'templates': templates(block), 'nodes': items}
    return result

def items_list(block):
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

def include_item(block):
    '''
    Renders one element.
    '''
    result = None
    if block.link and block.link.available:
        result = {'templates': templates(block), 'nodes': [block.link]}
    return result
