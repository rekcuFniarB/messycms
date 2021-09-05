from .models import Node
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
#from pprint import pprint
import re
import os
from django.conf import settings
from django.db.models import Q
from django.shortcuts import redirect
from . import plugins

## get requested node
def show_node(request, id=0, path=''):
    ''' /<str:path>/ request handler.'''
    
    lang_code = getattr(request, 'LANGUAGE_CODE', None)
    request_path = request.path.strip('/')
    node = None
    
    site_qs = Node.objects.filter(parent_id=None, sites__id=request.site.id)
    
    if request_path:
        path_list = [x for x in request_path.split('/') if x]
        last_slug = path_list[-1]
        
        ## Site root node queryset
        queryset = site_qs
        for path_part in path_list:
            queryset = queryset_children(queryset).filter(Q(slug=path_part) | Q(pk=str2int(path_part)), sites__id=request.site.id, available=True)
        node = queryset.first()
        
        if not node:
            ## Exact path search didn't find any node
            ## Trying to find anywhere
            queryset = site_qs
            if lang_code:
                queryset = queryset_children(queryset).filter(slug=lang_code, available=True, sites__id=request.site.id)
            queryset = queryset_descendants(queryset).filter(Q(slug=last_slug) | Q(pk=str2int(last_slug)), sites__id=request.site.id, available=True)
            if queryset.count() > 1:
                ## TODO show list of matches on 404 page
                raise Http404(f' Found multiple pages with slug {last_slug}.')
            
            node = queryset.first()
        
        if not node:
            raise Http404(f'Node "{last_slug}" not found')
        
        if node.id != str2int(last_slug) and node.slug != last_slug:
            raise Http404(f'Got wrong node "{node.id} {node.slug}" while "{last_slug}" expected.')
    
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
    
    if node.get_absolute_url().strip('/') != request_path:
        ## redirects to real path if node was moved.
        return redirect(node)
    
    ## If node has redirect property
    redirect_to = getattr(node.conf, 'redirect', None)
    ## Value may me string URL or Node instance
    if redirect_to:
        return redirect(redirect_to)
    
    #plugins.render(node, request)
    
    if node.link_id and node.type == 'content' and 'HTTP_X_REQUESTED_WITH' not in request.META:
        ## If link is defined, we use linked node as template for current
        node.link.context['include'] = node
        node = node.link
    
    if 'HTTP_X_REQUESTED_WITH' in request.META:
        templates = (
            f'{request.site.domain}/messycms/_node.html',
            'messycms/_node.html',
        )
    else:
        templates = (
            f'{request.site.domain}/messycms/node.html',
            'messycms/node.html',
        )
    
    return render(request, templates, {'node': node})

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
    if queryset:
        querysets = []
        for item in queryset:
            querysets.append(item.get_descendants())
        return combine_querysets(querysets)
    else:
        return queryset

def queryset_children(queryset):
    if queryset:
        querysets = []
        for item in queryset:
            querysets.append(item.get_children())
        return combine_querysets(querysets)
    else:
        return queryset
