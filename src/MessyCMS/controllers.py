from .models import Node
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
#from pprint import pprint
import re
import os
from django.conf import settings
from django.db.models import Q, Case, When
from django.shortcuts import redirect
from . import plugins
from .middleware import PluggableExternalAppsWrapper

def find_node(request):
    '''
    Find node by request
    '''
    path = request.path.strip('/')
    slug_list = [x for x in path.split('/') if x]
    last_slug = slug_list[-1]
    lang_code = getattr(request, 'LANGUAGE_CODE', None)
    lang_code_fallback = getattr(settings, 'LANGUAGE_CODE', 'en')
    
    qs = Node.objects.filter(parent_id=None, available=True, sites__id=request.site.id)
    
    for k, v in enumerate(slug_list):
        if k == 0 and lang_code and lang_code == v:
            ## children of requested lang node
            qs = qs.get_descendants().filter(Q(slug=lang_code) | Q(slug=lang_code_fallback), level=k+1, available=True, sites__id=request.site.id, type='content')
            qs = qs.annotate(lang_order=Case(When(slug=lang_code, then=3), When(slug=lang_code_fallback, then=2))).order_by('-lang_order').first().get_descendants(include_self=True)
        else:
            qs = qs.get_descendants().filter(Q(slug=v) | Q(pk=str2int(v)), level=k+1, available=True, type='content', sites__id=request.site.id)
    
    if settings.DEBUG:
        try:
            ## It fails sometimes
            print('SQL:', qs.query)
        except Exception as e:
            print('ERROR: could not print query:', e)
    
    node = qs.first()
    
    if not node:
        ## Not found by direct path, trying to find anywhere
        qs = Node.objects.filter(parent_id=None, available=True, sites__id=request.site.id).get_descendants().filter(Q(slug=last_slug) | Q(pk=str2int(last_slug)), available=True, sites__id=request.site.id)
        ## Check if all parents are available
        parents_all = qs.get_ancestors().count()
        parents_available = qs.get_ancestors().filter(available=True, sites__id=request.site.id).count()
        if parents_all == parents_available:
            node = qs.first()
        
        if settings.DEBUG:
            try:
                print('ANY NODE SQL:', qs.query)
            except Exception as e:
                print('ERROR: could not print query:', e)
    return node

## get requested node
def show_node(request, id=0, path=''):
    ''' /<str:path>/ request handler.'''
    request_path = request.path.strip('/')
    node = None
    
    if request_path:
        node = find_node(request)
        
        if not node:
            raise Http404(f'Node "{request_path}" not found')
        
        #if node.id != str2int(last_slug) and node.slug != last_slug:
            #raise Http404(f'Got wrong node "{node.id} {node.slug}" while "{last_slug}" expected.')
    
    elif id:
        ## This was for testing, actually not used
        try:
           node = Node.objects.get(pk=id)
        except Node.DoesNotExist:
           raise Http404(f'Requested node with ID {id} does not exist.')
    else:
        ## Main page requested
        node = Node.objects.filter(parent_id=None, sites__id=request.site.id).first()
        if not node:
            raise Http404(f'Main page for requested site {request.site} not found.')
    
    if node.type != 'content' or not node.available or node.slug.startswith('.') or (node.parent_id and node.parent.type == '.conf'):
        raise PermissionDenied
    
    if node.get_absolute_url() != request.path:
        ## redirects to real path if node was moved.
        return redirect(node)
    
    ## If node has redirect property
    redirect_to = getattr(node.conf, 'redirect', None)
    ## Value may me string URL or Node instance
    if redirect_to:
        return redirect(redirect_to)
    
    #plugins.render(node, request)
    
    templates = {
        'internal': (
            f'{request.site.domain}/messycms/_node.html',
            'messycms/_node.html',
        ),
        'full': (
            f'{request.site.domain}/messycms/node.html',
            'messycms/node.html',
        )
    }
    
    if 'HTTP_X_REQUESTED_WITH' in request.META:
        ## If is ajax request, don't extend base template
        template_type = 'internal'
    else: ## { not ajax
        template_type = 'full'
        
        if node.link_id:
            ## If link is defined, we use linked node as template for current
            node.link.context['include'] = node
            node = node.link
        else:
            ## Try to use first available template
            template_node = PluggableExternalAppsWrapper.get_template_node(request)
            if template_node:
                template_node.context['include'] = node
                node = template_node
    ## } endif nod ajax
    
    context = {'node': node, 'allnodes': []}
    ## "allnodes" will contain all rendered subnodes
    
    response = render(request, templates[template_type], context)
    
    if response.headers.get('Content-Type', '').startswith('text/html'):
        ## Inserting deferred nodes.
        ## For example, if node has slug "append-to-head"
        ## it will be appended to <head> element (inserted before closing </head> tag).
        for node in context['allnodes']:
            append_to = node.append_to()
            if append_to:
                append_render = render(request, templates['internal'], {'node': node})
                response.content = response.content.replace(append_to, append_render.content + append_to)
    
    return response

def str2int(string):
    try:
        value = int(string)
    except:
        value = 0
    return value

def combine_querysets(querysets=[]):
    '''
    Combine list of querysets into one queryset.
    querysets: iterable of querysets
    '''
    queryset = None
    if len(querysets):
        ## combining all querysets from previous for loop
        queryset = querysets.pop()
        for qs in querysets:
            if qs:
                queryset = queryset | qs
    return queryset

def queryset_descendants(queryset):
    '''
    Actually this function is not needed, unlike get_children,
    you can just use queryset.get_descendants()
    '''
    if queryset:
        querysets = []
        for item in queryset:
            querysets.append(item.get_descendants())
        return combine_querysets(querysets)
    else:
        return queryset

def queryset_children(queryset):
    '''
    Get children of queryset.
    '''
    if queryset:
        querysets = []
        for item in queryset:
            querysets.append(item.get_children())
        return combine_querysets(querysets)
    else:
        return queryset
