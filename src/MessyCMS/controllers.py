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

def find_node(request, path=''):
    '''
    Find node by request
        request: Request object
        path: string (optional, by default request.path will be used)
    '''
    if path:
        path = path.strip('/')
    else:
        path = request.path.strip('/')
    
    slug_list = [x for x in path.split('/') if x]
    last_slug = slug_list[-1]
    lang_code = getattr(request, 'LANGUAGE_CODE', None)
    qs = get_root_node_queryset(request)
    
    for k, v in enumerate(slug_list):
        if k > 0:
            qs = qs.get_descendants().filter(Q(slug=v) | Q(pk=plugins.str2int(v)), level=k+1, available=True, type='content', sites__id=request.site.id)
    
    #if settings.DEBUG:
        #try:
            ### It fails sometimes
            #print('SQL:', qs.query)
        #except Exception as e:
            #print('ERROR: could not print query:', e)
    
    node = qs.first()
    
    if not node:
        ## Not found by direct path, trying to find anywhere
        qs = Node.objects.filter(parent_id=None, available=True, sites__id=request.site.id).get_descendants().filter(Q(slug=last_slug) | Q(pk=plugins.str2int(last_slug)), available=True, sites__id=request.site.id)
        ## Check if all parents are available
        parents_all = qs.get_ancestors().count()
        parents_available = qs.get_ancestors().filter(available=True, sites__id=request.site.id).count()
        if parents_all == parents_available:
            node = qs.first()
        
        #if settings.DEBUG:
            #try:
                #print('ANY NODE SQL:', qs.query)
            #except Exception as e:
                #print('ERROR: could not print query:', e)
    return node

def get_root_node_queryset(request):
    '''
    Searches for current site and language root node.
    '''
    lang_code = getattr(request, 'LANGUAGE_CODE', None)
    lang_code_fallback = getattr(settings, 'LANGUAGE_CODE', 'en')
    ## Current site root
    site_qs = Node.objects.filter(parent_id=None, available=True, sites__id=request.site.id)
    if lang_code and request.path.startswith(f'/{lang_code}/'):
        qs = site_qs.get_descendants().filter(Q(slug=lang_code) | Q(slug=lang_code_fallback), level=1, available=True, sites__id=request.site.id, type='content')
        
        node = qs.annotate(lang_order=Case(When(slug=lang_code, then=3), When(slug=lang_code_fallback, then=2))).order_by('-lang_order').first()
        
        if node:
            qs = node.get_descendants(include_self=True)
        else:
            qs = site_qs
    else:
        qs = site_qs
    
    
    return qs

def raise_404_error(request, exception='Not found.'):
    '''
    Try to find node for showing 404 error or raise standard 404 exception as fallback.
    request:   Request object
    exception: string message.
    '''
    if not settings.DEBUG:
        node404 = get_root_node_queryset(request).get_descendants().filter(slug='http-status-code', short='404', available=True, type='.property', sites__id=request.site.id).first()
        
        if node404:
            node404 = node404.parent.parent
            node404.context['exception'] = exception
            return PluggableExternalAppsWrapper.prepare_response(request, node404)
        else:
            raise Http404(exception)
    else:
        raise Http404(exception)

## get requested node
def show_node(request, id=0, path=''):
    ''' /<str:path>/ request handler.'''
    request_path = request.path.strip('/')
    node = None
    
    if request_path:
        node = find_node(request)
        
        if not node:
            return raise_404_error(request, f'Node "{request_path}" not found')
        
        #if node.id != plugins.str2int(last_slug) and node.slug != last_slug:
            #return raise_404_error(request, f'Got wrong node "{node.id} {node.slug}" while "{last_slug}" expected.')
    
    elif id:
        ## This was for testing, actually not used
        try:
           node = Node.objects.get(pk=id)
        except Node.DoesNotExist:
           return raise_404_error(request, f'Requested node with ID {id} does not exist.')
    else:
        ## Main page requested
        node = Node.objects.filter(parent_id=None, sites__id=request.site.id).first()
        if not node:
            return raise_404_error(request, f'Main page for requested site {request.site} not found.')
    
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
    
    return PluggableExternalAppsWrapper.prepare_response(request, node)

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
